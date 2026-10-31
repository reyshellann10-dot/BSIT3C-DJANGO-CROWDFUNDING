from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import InvestmentForm
from .models import Investment, Transaction


# ─── INVEST NOW (modal form POST from user portal / browse campaigns) ─────────
@login_required(login_url='login')
def invest_now(request, project_pk):
    """Handle the Invest Now modal form submission."""
    from apps.campaigns.models import Project
    from apps.investors.models import Investor

    project  = get_object_or_404(Project, pk=project_pk, status='ongoing')

    # Every invest action belongs to the logged-in account's Investor profile.
    # Registration creates it, but accounts created another way may not have
    # one yet — link one automatically so the investment always has an owner.
    investor = getattr(request.user, 'investor_profile', None)
    if investor is None:
        full_name = f'{request.user.first_name} {request.user.last_name}'.strip()
        investor, _ = Investor.objects.get_or_create(
            user=request.user,
            defaults={'name': full_name or request.user.username},
        )

    # Determine where to redirect back to (portal or browse campaigns)
    referer   = request.META.get('HTTP_REFERER', '')
    back_url  = '/campaigns/projects/' if '/campaigns/projects' in referer else '/campaigns/portal/'

    if not investor:
        messages.error(
            request,
            'Your account does not have a linked investor profile. '
            'Please contact an administrator.'
        )
        return redirect(back_url)

    if request.method == 'POST':
        amount_raw     = request.POST.get('amount', '').strip()
        shares_raw     = request.POST.get('shares', '1').strip()
        payment_method = request.POST.get('payment_method', 'gcash').strip()

        # ── Validation ──────────────────────────────────────────────
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
            for msg in errors.values():
                messages.error(request, msg)
            return redirect(back_url)

        # ── Create the investment ────────────────────────────────────
        Investment.objects.create(
            investor=investor,
            project=project,
            amount=amount,
            shares=shares,
            payment_method=payment_method,
        )

        messages.success(
            request,
            f'✅ Investment of ₱{amount:,.2f} in "{project.title}" confirmed! '
            f'Payment via {dict(Investment.PAYMENT_CHOICES)[payment_method]}.'
        )
        return redirect(back_url)

    # GET — redirect back
    return redirect(back_url)


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

# --- INVESTMENT CRUD ---
@login_required(login_url='login')
def investment_create(request):
    form = InvestmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Investment created successfully.')
        return redirect('investments:investment_list')
    return render(request, 'investments/investment_form.html', {
        'form': form, 'title': 'Add Investment',
    })

@login_required(login_url='login')
def investment_update(request, pk):
    investment = get_object_or_404(Investment, pk=pk)
    form = InvestmentForm(request.POST or None, instance=investment)
    if request.method == 'POST' and form.is_valid():
        form.save()
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