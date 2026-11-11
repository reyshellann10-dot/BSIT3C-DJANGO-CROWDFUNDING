from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

User = get_user_model()

MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION = timedelta(minutes=1)
INVALID_LOGIN_MESSAGE = 'Invalid username or password.'
LOCKED_MESSAGE = 'Too many failed attempts. Locked for 1 minute.'


def _reset_lock_state(request):
    request.session['failed_attempts'] = 0
    request.session['lock_time'] = None


def _get_lock_state(request):
    failed_attempts = request.session.get('failed_attempts', 0)
    lock_time = request.session.get('lock_time')

    if not lock_time:
        return failed_attempts, None

    try:
        unlock_time = timezone.datetime.fromisoformat(lock_time)
    except (TypeError, ValueError):
        _reset_lock_state(request)
        return 0, None

    if timezone.now() < unlock_time:
        remaining = int((unlock_time - timezone.now()).total_seconds())
        return failed_attempts, remaining

    _reset_lock_state(request)
    return 0, None


def _set_lock_state(request):
    lock_until = timezone.now() + LOCK_DURATION
    request.session['failed_attempts'] = MAX_FAILED_ATTEMPTS
    request.session['lock_time'] = lock_until.isoformat()
    return int(LOCK_DURATION.total_seconds())


def _validate_registration_data(data):
    errors = {}

    username = data.get('username', '').strip()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')

    if not username:
        errors['username'] = 'Username is required.'
    elif User.objects.filter(username=username).exists():
        errors['username'] = 'Username already taken.'

    if not first_name:
        errors['first_name'] = 'First name is required.'

    if not last_name:
        errors['last_name'] = 'Last name is required.'

    if not email:
        errors['email'] = 'Email is required.'
    else:
        try:
            validate_email(email)
        except ValidationError:
            errors['email'] = 'Enter a valid email address.'
        else:
            if User.objects.filter(email=email).exists():
                errors['email'] = 'Email already registered.'

    if not password:
        errors['password'] = 'Password is required.'
    elif len(password) < 8:
        errors['password'] = 'Password must be at least 8 characters.'
    else:
        try:
            validate_password(password)
        except ValidationError as exc:
            errors['password'] = ' '.join(exc.messages)

    if password != confirm_password:
        errors['confirm_password'] = 'Passwords do not match.'

    return errors


@require_http_methods(['GET', 'POST'])
def admin_login_view(request):
    """Separate login page for staff/superusers only."""
    # Redirect already-authenticated admins straight to the dashboard
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('/campaigns/')
        # Authenticated but not admin — send to user portal
        return redirect('/campaigns/portal/')

    failed_attempts, remaining_lock = _get_lock_state(request)

    if remaining_lock:
        messages.error(request, LOCKED_MESSAGE)
        return render(request, 'auth/admin_login.html', {'lock_remaining': remaining_lock})

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_staff or user.is_superuser:
                # Valid admin — log in and go to dashboard
                login(request, user)
                _reset_lock_state(request)
                return redirect('/campaigns/')
            else:
                # Valid credentials but not an admin — reject, do NOT log in
                failed_attempts += 1
                request.session['failed_attempts'] = failed_attempts
                return render(request, 'auth/admin_login.html', {
                    'error': 'You are not authorized to access the admin panel.'
                })
        else:
            # Wrong credentials
            failed_attempts += 1
            request.session['failed_attempts'] = failed_attempts
            if failed_attempts >= MAX_FAILED_ATTEMPTS:
                remaining = _set_lock_state(request)
                messages.error(request, LOCKED_MESSAGE)
                return render(request, 'auth/admin_login.html', {'lock_remaining': remaining})
            messages.error(request, INVALID_LOGIN_MESSAGE)
            return render(request, 'auth/admin_login.html')

    return render(request, 'auth/admin_login.html')


@require_http_methods(['GET', 'POST'])
def login_view(request):
    failed_attempts, remaining_lock = _get_lock_state(request)
    if remaining_lock:
        messages.error(request, LOCKED_MESSAGE)
        return render(request, 'auth/login.html', {'lock_remaining': remaining_lock})

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Successful login — route by role
            login(request, user)
            _reset_lock_state(request)
            if user.is_staff or user.is_superuser:
                return redirect('/campaigns/')       # Admin dashboard
            # Return the user where they came from (e.g. "Login to Invest")
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect('/campaigns/portal/')    # User portal
        else:
            # Failed login attempt
            failed_attempts += 1
            request.session['failed_attempts'] = failed_attempts
            if failed_attempts >= MAX_FAILED_ATTEMPTS:
                remaining = _set_lock_state(request)
                messages.error(request, LOCKED_MESSAGE)
                return render(request, 'auth/login.html', {'lock_remaining': remaining})
            else:
                messages.error(request, INVALID_LOGIN_MESSAGE)
                return render(request, 'auth/login.html')

    return render(request, 'auth/login.html')


@require_http_methods(['GET', 'POST'])
def register_view(request):
    if request.method == 'POST':
        errors = _validate_registration_data(request.POST)
        if not errors:
            first_name = request.POST.get('first_name', '').strip()
            last_name  = request.POST.get('last_name', '').strip()

            user = User.objects.create_user(
                username=request.POST.get('username'),
                email=request.POST.get('email'),
                password=request.POST.get('password'),
                first_name=first_name,
                last_name=last_name,
            )

            # Auto-create a linked Investor profile for every new user
            try:
                from apps.investors.models import Investor
                Investor.objects.create(
                    user=user,
                    name=f"{first_name} {last_name}".strip() or user.username,
                    # Keep the insert independent of the DB's NULL handling.
                    contact='',
                    address='',
                )
            except Exception:
                # If profile creation fails for any reason, the user account
                # is still valid — admin can link the profile manually later.
                pass

            login(request, user)
            return redirect('/campaigns/portal/')
        else:
            return render(request, 'auth/register.html', {'errors': errors, 'data': request.POST})

    return render(request, 'auth/register.html')


@require_http_methods(['GET', 'POST'])
def logout_view(request):
    logout(request)
    return redirect('/')   # Back to public landing page


def home(request):
    """Public landing page — no login required."""
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('/campaigns/')
        return redirect('/campaigns/portal/')

    # Real platform stats for the landing page
    from django.db.models import Sum as _Sum
    from apps.campaigns.models import Project
    from apps.investors.models import Investor
    from apps.investments.models import Investment

    total_projects  = Project.objects.filter(status='ongoing').count()
    total_investors = Investor.objects.count()
    total_raised    = Investment.objects.aggregate(t=_Sum('amount'))['t'] or 0

    # Live campaigns listed on the landing page (newest first).
    projects = Project.objects.filter(status='ongoing').order_by('-created_at')

    return render(request, 'home.html', {
        'total_projects':  total_projects,
        'total_investors': total_investors,
        'total_raised':    total_raised,
        'projects':        projects,
    })


def how_it_works(request):
    """How It Works page — public, including for logged-in users."""
    return render(request, 'how_it_works.html')


def features(request):
    """Platform Features page — public, including for logged-in users."""
    return render(request, 'features.html')


def roles(request):
    """Three Roles page — public, including for logged-in users."""
    return render(request, 'roles.html')