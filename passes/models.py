import uuid
from io import BytesIO

import qrcode
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse


class Event(models.Model):
    """A parent event, e.g. 'Tech Conference 2026'."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    venue = models.CharField(max_length=200)
    banner = models.ImageField(upload_to='event_banners/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='events_created')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('passes:event_detail', args=[self.pk])


class EventSession(models.Model):
    """A specific date + time slot for an event that a user can register a pass for."""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='sessions')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(blank=True, null=True)
    capacity = models.PositiveIntegerField(default=0, help_text="0 = unlimited")

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.event.title} — {self.date} {self.start_time.strftime('%I:%M %p')}"

    @property
    def seats_taken(self):
        return self.eventpass_set.exclude(status='cancelled').count()

    @property
    def is_full(self):
        return self.capacity > 0 and self.seats_taken >= self.capacity


class EventPass(models.Model):
    """An issued pass/ticket for a specific attendee + session, identified by a unique QR code.

    An attendee can either be:
    - `holder` — a logged-in User who self-registered, OR
    - `member` — a Member record added manually by the organizer (name/address/phone etc.)
    Exactly one of the two should be set.
    """
    STATUS_CHOICES = (
        ('valid', 'Valid'),
        ('used', 'Used'),
        ('cancelled', 'Cancelled'),
    )
    PASS_TYPE_CHOICES = (
        ('general', 'General'),
        ('vip', 'VIP'),
    )

    session = models.ForeignKey(EventSession, on_delete=models.CASCADE, related_name='eventpass_set')
    holder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='passes', null=True, blank=True)
    member = models.OneToOneField(
        'Member', on_delete=models.CASCADE, related_name='event_pass', null=True, blank=True
    )
    pass_type = models.CharField(max_length=10, choices=PASS_TYPE_CHOICES, default='general')
    pass_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    qr_image = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='valid')
    issued_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(blank=True, null=True)
    scanned_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='scanned_passes'
    )

    class Meta:
        ordering = ['-issued_at']

    def __str__(self):
        return f"Pass {str(self.pass_code)[:8]} — {self.display_name} — {self.session}"

    @property
    def display_name(self):
        if self.holder_id:
            return self.holder.get_full_name() or self.holder.username
        if self.member_id:
            return self.member.full_name
        return "Unknown"

    @property
    def display_phone(self):
        return self.member.phone_number if self.member_id else getattr(self.holder.profile, 'phone_number', '')

    @property
    def is_vip(self):
        return self.pass_type == 'vip'

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and not self.qr_image:
            self.generate_qr_code()

    def generate_qr_code(self):
        """Encodes the unique pass_code into a QR image and attaches it to this pass.
        VIP passes get a gold-toned QR to visually stand out even before scanning."""
        fill_color = "#8a6d00" if self.is_vip else "#0d1b2a"
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(str(self.pass_code))
        qr.make(fit=True)
        img = qr.make_image(fill_color=fill_color, back_color="white")

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        filename = f"pass_{self.pass_code}.png"
        self.qr_image.save(filename, ContentFile(buffer.getvalue()), save=True)

    @property
    def is_valid(self):
        return self.status == 'valid'


class Member(models.Model):
    """An attendee added manually by the organizer (no login account needed).
    e.g. bulk-adding a guest list with name, father's name, address, phone, company.
    """
    PASS_TYPE_CHOICES = EventPass.PASS_TYPE_CHOICES

    session = models.ForeignKey(EventSession, on_delete=models.CASCADE, related_name='members')
    full_name = models.CharField(max_length=150)
    father_name = models.CharField(max_length=150, verbose_name="Father's Name")
    address = models.TextField()
    phone_number = models.CharField(max_length=20)
    company_name = models.CharField(max_length=150, blank=True, verbose_name="Company Name (optional)")
    pass_type = models.CharField(max_length=10, choices=PASS_TYPE_CHOICES, default='general')
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='members_added')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.get_pass_type_display()}) — {self.session}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and not hasattr(self, 'event_pass'):
            EventPass.objects.create(session=self.session, member=self, pass_type=self.pass_type)
