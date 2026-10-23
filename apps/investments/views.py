from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import InvestmentForm
from .models import Investment, Transaction

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