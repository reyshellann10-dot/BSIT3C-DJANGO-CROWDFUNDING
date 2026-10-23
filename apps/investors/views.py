from django.shortcuts import render, redirect, get_object_or_404 # Idinagdag ang get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Investor
from .forms import InvestorForm

@login_required(login_url='login')
def dashboard(request):
    query = request.GET.get('q', '').strip()
    qs = Investor.objects.all().order_by('name')
    if query:
        qs = qs.filter(Q(name__icontains=query) | Q(contact__icontains=query))
    
    paginator = Paginator(qs, 10)
    investors = paginator.get_page(request.GET.get('page', 1))
    
    return render(request, 'investors/dashboard.html', {
        'investors': investors, 
        'query': query,
    })

@login_required(login_url='login')
def investor_create(request):
    form = InvestorForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        investor = form.save()
        messages.success(request, f'Investor "{investor.name}" created successfully.')
        return redirect('investors:dashboard')
    return render(request, 'investors/investor_form.html', {
        'form': form, 'title': 'Add Investor',
    })

@login_required(login_url='login')
def investor_update(request, pk):
    investor = get_object_or_404(Investor, pk=pk)
    form = InvestorForm(request.POST or None, instance=investor)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Investor updated.')
        return redirect('investors:dashboard')
    return render(request, 'investors/investor_form.html', {
        'form': form, 'title': 'Edit Investor',
    })

@login_required(login_url='login')
def investor_delete(request, pk):
    investor = get_object_or_404(Investor, pk=pk)
    if request.method == 'POST':
        investor.delete()
        messages.success(request, 'Investor deleted.')
    return redirect('investors:dashboard')