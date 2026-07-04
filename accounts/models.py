from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Extends the built-in User with role-based access.

    ATTENDEE  -> can register for events and hold passes
    SCANNER   -> staff who can operate the entry scanner
    ORGANIZER -> can create/manage events (also gets Django is_staff)
    """
    ROLE_CHOICES = (
        ('attendee', 'Attendee'),
        ('scanner', 'Scanner Staff'),
        ('organizer', 'Organizer'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='attendee')
    phone_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def can_scan(self):
        return self.role in ('scanner', 'organizer') or self.user.is_staff

    @property
    def can_manage_events(self):
        return self.role == 'organizer' or self.user.is_staff


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
