from django.contrib import admin
from .models import Event, EventSession, EventPass, Member


class EventSessionInline(admin.TabularInline):
    model = EventSession
    extra = 1


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'venue', 'is_active', 'created_by', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'venue')
    inlines = [EventSessionInline]


@admin.register(EventSession)
class EventSessionAdmin(admin.ModelAdmin):
    list_display = ('event', 'date', 'start_time', 'end_time', 'capacity', 'seats_taken')
    list_filter = ('date', 'event')


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'father_name', 'phone_number', 'company_name', 'pass_type', 'session', 'added_by')
    list_filter = ('pass_type', 'session__event')
    search_fields = ('full_name', 'father_name', 'phone_number', 'company_name')


@admin.register(EventPass)
class EventPassAdmin(admin.ModelAdmin):
    list_display = ('pass_code', 'display_name', 'pass_type', 'session', 'status', 'issued_at', 'used_at', 'scanned_by')
    list_filter = ('status', 'pass_type')
    search_fields = ('pass_code', 'holder__username', 'member__full_name')
    readonly_fields = ('pass_code', 'qr_image', 'issued_at')
