from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import InvestmentForm
from .models import Investment, Transaction


# ─── TRANSACTION RECEIPT ──────────────────────────────────────────────────────
@login_required(login_url='login')
def transaction_receipt(request, pk):
    """Printable receipt for a single investment.
    Admins can view any receipt; regular users only their own."""
    investment = get_object_or_404(
        Investment.objects.select_related('investor', 'project'),
        pk=pk
    )
    if not (request.user.is_staff or request.user.is_superuser):
        investor = getattr(request.user, 'investor_profile', None)
        if not investor or investment.investor != investor:
            messages.error(request, 'You are not authorised to view this receipt.')
            return redirect('investments:my_portfolio')
    return render(request, 'investments/receipt.html', {'inv': investment})


# ─── INVEST NOW — Step 1: validate, store in session, return checkout URL ─────
@login_required(login_url='login')
def invest_now(request, project_pk):
    """Validates the modal form, stores pending investment in session,
    and returns the checkout URL via JSON. Does NOT save to DB yet."""
    from apps.campaigns.models import Project
    from django.http import JsonResponse

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    project = get_object_or_404(Project, pk=project_pk, status='ongoing')

    # Auto-create investor profile if missing
    investor = _get_or_create_investor(request.user)

    referer  = request.META.get('HTTP_REFERER', '')
    back_url = '/campaigns/projects/' if '/campaigns/projects' in referer else '/campaigns/portal/'

    if request.method != 'POST':
        if is_ajax:
            return JsonResponse({'ok': False, 'error': 'POST required.'}, status=405)
        return redirect(back_url)

    # ── Validate inputs ──────────────────────────────────────────────
    amount_raw     = request.POST.get('amount', '').strip()
    shares_raw     = request.POST.get('shares', '1').strip()
    payment_method = request.POST.get('payment_method', 'gcash').strip()

    errors = {}
    try:
        amount = Decimal(amount_raw)
        if amount <= 0:
            errors['amount'] = 'Amount must be greater than zero.'
    except (InvalidOperation, ValueError, TypeError):
        errors['amount'] = 'Please enter a valid amount.'
        amount = Decimal('0')

    try:
        shares = int(shares_raw)
        if shares < 1:
            errors['shares'] = 'Shares must be at least 1.'
    except (ValueError, TypeError):
        errors['shares'] = 'Please enter a valid number of shares.'
        shares = 1

    valid_methods = [c[0] for c in Investment.PAYMENT_CHOICES]
    if payment_method not in valid_methods:
        payment_method = 'gcash'

    if errors:
        if is_ajax:
            return JsonResponse({'ok': False, 'errors': errors}, status=400)
        for msg in errors.values():
            messages.error(request, msg)
        return redirect(back_url)

    # ── Check campaign funding cap ───────────────────────────────────
    remaining = project.target_amount - project.total_raised
    if remaining <= 0:
        err = 'This campaign has already reached its target amount.'
        if is_ajax:
            return JsonResponse({'ok': False, 'errors': {'amount': err}}, status=400)
        messages.error(request, err)
        return redirect(back_url)

    if amount > remaining:
        err = (
            f'Your investment of ₱{amount:,.2f} exceeds the remaining '
            f'fundable amount of ₱{remaining:,.2f} for this campaign.'
        )
        if is_ajax:
            return JsonResponse({'ok': False, 'errors': {'amount': err}}, status=400)
        messages.error(request, err)
        return redirect(back_url)

    # ── Store pending investment in session (not saved to DB yet) ────
    request.session['pending_investment'] = {
        'project_pk':     project_pk,
        'amount':         str(amount),
        'shares':         shares,
        'payment_method': payment_method,
        'back_url':       back_url,
    }

    checkout_url = f'/investments/checkout/{project_pk}/'

    if is_ajax:
        return JsonResponse({'ok': True, 'checkout_url': checkout_url})

    return redirect(checkout_url)


# ─── CHECKOUT — Step 2: show payment gateway page ─────────────────────────────
@login_required(login_url='login')
def checkout(request, project_pk):
    """Step 2 — Show the payment gateway page, then save on final confirm."""
    from apps.campaigns.models import Project

    project = get_object_or_404(Project, pk=project_pk, status='ongoing')

    # Auto-create investor profile if missing
    investor = _get_or_create_investor(request.user)

    pending = request.session.get('pending_investment')
    back_url = '/campaigns/projects/'

    # ── GET: render payment gateway ──────────────────────────────────
    if request.method == 'GET':
        if not pending or str(pending.get('project_pk')) != str(project_pk):
            messages.error(request, 'Session expired. Please start again.')
            return redirect(back_url)

        amount         = Decimal(pending['amount'])
        shares         = pending['shares']
        payment_method = pending['payment_method']
        profit         = (amount * project.profit_rate) / 100
        total_return   = amount + profit
        pay_label      = dict(Investment.PAYMENT_CHOICES).get(payment_method, payment_method)

        return render(request, 'investments/payment_process.html', {
            'project':          project,
            'amount':           amount,
            'shares':           shares,
            'payment_method':   payment_method,
            'pay_label':        pay_label,
            'profit':           profit,
            'total_return':     total_return,
            'bank_errors':      [],
            'prev_sender_bank': '',
            'prev_sender_name': '',
            'prev_reference':   '',
        })

    # ── POST: final confirm → save investment ────────────────────────
    if not pending or str(pending.get('project_pk')) != str(project_pk):
        messages.error(request, 'Session expired. Please start again.')
        return redirect(back_url)

    amount         = Decimal(pending['amount'])
    shares         = pending['shares']
    payment_method = pending['payment_method']

    # Re-check cap at the moment of final save (someone else may have funded it)
    remaining = project.target_amount - project.total_raised
    if remaining <= 0 or amount > remaining:
        del request.session['pending_investment']
        messages.error(
            request,
            'Sorry, this campaign reached its target while you were checking out. '
            'Your payment was not processed.'
        )
        return redirect(back_url)

    # Collect extra fields from the payment form
    mobile_number    = request.POST.get('mobile_number', '').strip()
    reference_number = request.POST.get('reference_number', '').strip()
    sender_name      = request.POST.get('sender_name', '').strip()
    sender_bank      = request.POST.get('sender_bank', '').strip()

    # ── Bank transfer strict validation ─────────────────────────────
    if payment_method == 'bank_transfer':
        VALID_BANKS = {
            'BDO','BPI','Metrobank','Landbank','DBP','PNB',
            'Unionbank','RCBC','Eastwest','Chinabank','Security Bank',
            'GCash','Maya','Other',
        }
        bank_errors = []
        if not sender_bank or sender_bank not in VALID_BANKS:
            bank_errors.append('Please select a valid bank from the dropdown.')
        if not sender_name:
            bank_errors.append('Sender / Account Name is required.')
        if not reference_number:
            bank_errors.append('Bank Reference / Transaction Number is required.')

        if bank_errors:
            # Re-render the payment page with the error list
            amount_d       = Decimal(pending['amount'])
            shares_        = pending['shares']
            profit         = (amount_d * project.profit_rate) / 100
            total_return   = amount_d + profit
            pay_label      = dict(Investment.PAYMENT_CHOICES).get(payment_method, payment_method)
            return render(request, 'investments/payment_process.html', {
                'project':        project,
                'amount':         amount_d,
                'shares':         shares_,
                'payment_method': payment_method,
                'pay_label':      pay_label,
                'profit':         profit,
                'total_return':   total_return,
                'bank_errors':    bank_errors,
                # Repopulate submitted values
                'prev_sender_bank': sender_bank,
                'prev_sender_name': sender_name,
                'prev_reference':   reference_number,
            })

        # Store bank name inside reference_number for the receipt
        reference_number = f'[{sender_bank}] {reference_number}'

    # Bank transfer → pending verification; all others → confirmed immediately
    is_bank = payment_method == 'bank_transfer'
    inv_status = 'pending_verification' if is_bank else 'confirmed'

    investment = Investment.objects.create(
        investor=investor,
        project=project,
        amount=amount,
        shares=shares,
        payment_method=payment_method,
        status=inv_status,
        reference_number=reference_number,
        sender_name=sender_name,
    )

    # Update project.current_amount to reflect the new investment
    from django.db.models import F
    project.__class__.objects.filter(pk=project.pk).update(
        current_amount=F('current_amount') + amount
    )

    # Clear session so the same pending data can't be reused
    del request.session['pending_investment']

    return redirect(f'/investments/receipt/{investment.pk}/?paid=1')


# ─── MY PORTFOLIO (logged-in user's own investments) ──────────────────────────
@login_required(login_url='login')
def my_portfolio(request):
    """Shows only investments belonging to the currently logged-in user
    via their linked Investor profile."""
    investor = getattr(request.user, 'investor_profile', None)

    if investor:
        investments = (
            Investment.objects
            .filter(investor=investor)
            .select_related('project')
            .order_by('-created_at')
        )
        total_invested = investments.aggregate(t=Sum('amount'))['t'] or 0
        total_profit   = sum(inv.profit        for inv in investments)
        total_return   = sum(inv.total_return   for inv in investments)
        total_shares   = sum(inv.shares         for inv in investments)
    else:
        investments    = []
        total_invested = 0
        total_profit   = 0
        total_return   = 0
        total_shares   = 0

    return render(request, 'investments/my_portfolio.html', {
        'investor':      investor,
        'investments':   investments,
        'total_invested': total_invested,
        'total_profit':   total_profit,
        'total_return':   total_return,
        'total_shares':   total_shares,
    })

# --- DASHBOARD ---
@login_required(login_url='login')
def dashboard(request):
    investments = Investment.objects.all().order_by('-created_at')
    total_investments = investments.count()
    total_amount = investments.aggregate(total=Sum('amount'))['total'] or 0
    
    return render(request, 'investments/dashboard.html', {
        'investments': investments,
        'total_investments': total_investments,
        'total_amount': total_amount,
    })

# --- INVESTMENT LIST (MAY SEARCH NA) ---
@login_required(login_url='login')
def investment_list(request):
    query = request.GET.get('q', '').strip()
    qs = Investment.objects.select_related('investor', 'project').order_by('-created_at')
    
    # Logic para sa Search
    if query:
        qs = qs.filter(
            Q(investor__name__icontains=query) | 
            Q(project__title__icontains=query)
        )
        
    paginator = Paginator(qs, 10)
    investments = paginator.get_page(request.GET.get('page', 1))
    
    return render(request, 'investments/investment_list.html', {
        'investments': investments,
        'query': query,
    })

def _get_or_create_investor(user):
    """Return the Investor profile for a user, creating one if needed."""
    from apps.investors.models import Investor
    investor = getattr(user, 'investor_profile', None)
    if investor is None:
        full_name = f'{user.first_name} {user.last_name}'.strip()
        investor, _ = Investor.objects.get_or_create(
            user=user,
            defaults={
                'name':    full_name or user.username,
                'contact': 'N/A',
                'address': '',
            },
        )
    return investor


# --- INVESTMENT CRUD ---
@login_required(login_url='login')
def investment_create(request):
    from django.db.models import F
    form = InvestmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        investor = _get_or_create_investor(request.user)
        investment = form.save(commit=False)
        investment.investor = investor
        investment.save()
        # Keep project.current_amount in sync
        investment.project.__class__.objects.filter(pk=investment.project.pk).update(
            current_amount=F('current_amount') + investment.amount
        )
        messages.success(request, 'Investment created successfully.')
        return redirect('investments:investment_list')
    return render(request, 'investments/investment_form.html', {
        'form': form, 'title': 'Add Investment',
    })

@login_required(login_url='login')
def investment_update(request, pk):
    from django.db.models import F
    investment = get_object_or_404(Investment, pk=pk)
    old_amount = investment.amount          # capture before the form overwrites it
    form = InvestmentForm(request.POST or None, instance=investment)
    if request.method == 'POST' and form.is_valid():
        updated = form.save(commit=False)
        # Ensure investor is never cleared
        if not updated.investor_id:
            updated.investor = _get_or_create_investor(request.user)
        updated.save()
        # Adjust current_amount by the delta (new - old)
        delta = updated.amount - old_amount
        if delta != 0:
            updated.project.__class__.objects.filter(pk=updated.project.pk).update(
                current_amount=F('current_amount') + delta
            )
        messages.success(request, 'Investment updated successfully.')
        return redirect('investments:investment_list')
    return render(request, 'investments/investment_form.html', {
        'form': form, 'title': 'Edit Investment',
    })

@login_required(login_url='login')
def investment_delete(request, pk):
    investment = get_object_or_404(Investment, pk=pk)
    if request.method == 'POST':
        messages.success(request, 'Investment deleted successfully.')
        investment.delete()
    return redirect('investments:investment_list')