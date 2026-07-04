import json
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import Event, EventSession, EventPass, Member
from .forms import EventForm, EventSessionForm, RegisterPassForm, MemberFormSet


def scanner_required(view_func):
    """Restrict a view to users whose profile allows scanning entry passes."""
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        profile = getattr(request.user, 'profile', None)
        if not (profile and profile.can_scan):
            messages.error(request, "You don't have permission to access the scanner.")
            return redirect('passes:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


def organizer_required(view_func):
    """Restrict a view to users who can create/manage events."""
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        profile = getattr(request.user, 'profile', None)
        if not (profile and profile.can_manage_events):
            messages.error(request, "You don't have permission to manage events.")
            return redirect('passes:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    profile = getattr(request.user, 'profile', None)
    context = {
        'profile': profile,
        'upcoming_events': Event.objects.filter(is_active=True).prefetch_related('sessions')[:6],
        'my_passes_count': request.user.passes.filter(status='valid').count(),
    }
    if profile and profile.can_scan:
        context['recent_scans'] = EventPass.objects.filter(
            scanned_by=request.user, status='used'
        ).select_related('session__event', 'holder').order_by('-used_at')[:8]
    return render(request, 'passes/dashboard.html', context)


# ---------------------------------------------------------------------------
# Events (public browsing + organizer management)
# ---------------------------------------------------------------------------

@login_required
def event_list(request):
    events = Event.objects.filter(is_active=True).prefetch_related('sessions')
    return render(request, 'passes/event_list.html', {'events': events})


@login_required
def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    return render(request, 'passes/event_detail.html', {'event': event})


@organizer_required
def event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            messages.success(request, f"Event '{event.title}' created. Now add at least one date/time session.")
            return redirect('passes:session_create', event_id=event.pk)
    else:
        form = EventForm()
    return render(request, 'passes/event_form.html', {'form': form})


@organizer_required
def session_create(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if request.method == 'POST':
        form = EventSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.event = event
            session.save()
            messages.success(request, "Session added successfully.")
            if 'add_another' in request.POST:
                return redirect('passes:session_create', event_id=event.pk)
            return redirect('passes:event_detail', pk=event.pk)
    else:
        form = EventSessionForm()
    return render(request, 'passes/session_form.html', {'form': form, 'event': event})


# ---------------------------------------------------------------------------
# Members (organizer adds attendees manually — with VIP option)
# ---------------------------------------------------------------------------

@organizer_required
def member_list(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    members = Member.objects.filter(session__event=event).select_related('session', 'event_pass')
    return render(request, 'passes/member_list.html', {'event': event, 'members': members})


@organizer_required
def member_create(request, session_id):
    """Add one or many members at once for a session. Each filled-in row generates
    its own Member + auto-generated QR pass (General or VIP)."""
    session = get_object_or_404(EventSession, pk=session_id)

    if request.method == 'POST':
        formset = MemberFormSet(request.POST)
        if formset.is_valid():
            created_count = 0
            for form in formset:
                if not form.has_changed() or not form.cleaned_data:
                    continue
                if form.cleaned_data.get('DELETE'):
                    continue
                member = form.save(commit=False)
                member.session = session
                member.added_by = request.user
                member.save()
                created_count += 1

            if created_count:
                messages.success(request, f"{created_count} member(s) added — passes generated successfully.")
            else:
                messages.info(request, "No member details were filled in.")
            return redirect('passes:member_list', event_id=session.event_id)
    else:
        formset = MemberFormSet()

    return render(request, 'passes/member_form.html', {'formset': formset, 'session': session})


@organizer_required
def member_pass_detail(request, pk):
    member = get_object_or_404(Member, pk=pk)
    event_pass = member.event_pass
    return render(request, 'passes/pass_detail.html', {'p': event_pass, 'organizer_view': True})


# ---------------------------------------------------------------------------
# Pass registration & viewing
# ---------------------------------------------------------------------------

@login_required
def register_pass(request, event_id):
    event = get_object_or_404(Event, pk=event_id, is_active=True)

    if request.method == 'POST':
        form = RegisterPassForm(request.POST, event=event)
        if form.is_valid():
            session = form.cleaned_data['session']
            if session.is_full:
                messages.error(request, "Sorry, this date/time slot is fully booked.")
                return redirect('passes:event_detail', pk=event.pk)

            already = EventPass.objects.filter(
                session=session, holder=request.user
            ).exclude(status='cancelled').exists()
            if already:
                messages.info(request, "You already have a pass for this date & time.")
            else:
                event_pass = EventPass.objects.create(session=session, holder=request.user)
                messages.success(request, "Your pass has been generated! Show the QR code at entry.")
                return redirect('passes:pass_detail', pk=event_pass.pk)
            return redirect('passes:my_passes')
    else:
        form = RegisterPassForm(event=event)

    return render(request, 'passes/register_pass.html', {'form': form, 'event': event})


@login_required
def my_passes(request):
    passes = request.user.passes.select_related('session__event').all()
    return render(request, 'passes/my_passes.html', {'passes': passes})


@login_required
def pass_detail(request, pk):
    event_pass = get_object_or_404(EventPass, pk=pk, holder=request.user)
    return render(request, 'passes/pass_detail.html', {'p': event_pass})


# ---------------------------------------------------------------------------
# Scanner (entry validation)
# ---------------------------------------------------------------------------

@scanner_required
def scanner_view(request):
    return render(request, 'passes/scanner.html')


@scanner_required
@require_POST
def scan_api(request):
    """AJAX endpoint called by the browser QR scanner with the decoded pass_code."""
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = request.POST

    pass_code = (payload.get('pass_code') or '').strip()
    if not pass_code:
        return JsonResponse({'ok': False, 'result': 'error', 'message': 'No pass code received.'}, status=400)

    try:
        event_pass = EventPass.objects.select_related('session__event', 'holder').get(pass_code=pass_code)
    except (EventPass.DoesNotExist, ValueError, ValidationError):
        return JsonResponse({'ok': False, 'result': 'invalid', 'message': 'This QR code is not a recognized pass.'})

    session = event_pass.session
    data = {
        'holder_name': event_pass.display_name,
        'event_title': session.event.title,
        'venue': session.event.venue,
        'date': session.date.strftime('%d %b %Y'),
        'time': session.start_time.strftime('%I:%M %p'),
        'status': event_pass.status,
        'pass_type': event_pass.pass_type,
        'is_vip': event_pass.is_vip,
    }

    if event_pass.status == 'cancelled':
        return JsonResponse({'ok': False, 'result': 'cancelled', 'message': 'This pass has been cancelled.', **data})

    if event_pass.status == 'used':
        return JsonResponse({
            'ok': False, 'result': 'already_used',
            'message': f"Already used at {event_pass.used_at.strftime('%d %b %Y, %I:%M %p')}.",
            **data,
        })

    # Valid pass -> mark as used
    event_pass.status = 'used'
    event_pass.used_at = timezone.now()
    event_pass.scanned_by = request.user
    event_pass.save(update_fields=['status', 'used_at', 'scanned_by'])

    return JsonResponse({'ok': True, 'result': 'allowed', 'message': 'Entry approved. Welcome!', **data})
