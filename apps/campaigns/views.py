import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render

from .models import Project
from .forms import ProjectForm
from apps.investments.models import Investment
from apps.investors.models import Investor

# --- DASHBOARD ---
@login_required(login_url='login')
def dashboard(request):
    # 1. Basic Stats
    total_projects = Project.objects.count()
    total_investments = Investment.objects.count()
    total_amount = Investment.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_investors = Investor.objects.count()

    # 2. Recent Data
    recent_projects = Project.objects.all().order_by('-id')[:5] 
    recent_investments = Investment.objects.all().order_by('-id')[:5]

    # 3. Data para sa Pie Chart (Project Status)
    status_data = Project.objects.values('status').annotate(count=Count('id'))
    status_labels = [item['status'].title() for item in status_data]
    status_counts = [item['count'] for item in status_data]

    # 4. Data para sa Bar Chart (Investments per Month)
    monthly_data = Investment.objects.annotate(month=TruncMonth('created_at')).values('month').annotate(total=Sum('amount')).order_by('month')
    
    if not monthly_data:
        chart_labels = ['No Data']
        chart_amounts = [0]
    else:
        chart_labels = [item['month'].strftime('%b %Y') for item in monthly_data]
        # Ginagawa nating float para madaling i-plot sa chart
        chart_amounts = [float(item['total']) for item in monthly_data]

    return render(request, 'campaigns/dashboard.html', {
        'total_projects': total_projects,
        'recent_projects': recent_projects,
        'recent_investments': recent_investments,
        'total_investments': total_investments,
        'total_amount': total_amount,
        'total_investors': total_investors,
        'chart_labels': json.dumps(chart_labels),
        'chart_amounts': json.dumps(chart_amounts),
        'status_labels': json.dumps(status_labels),
        'status_counts': json.dumps(status_counts),
    })

# --- PROJECT CRUD ---
@login_required(login_url='login')
def project_list(request):
    query = request.GET.get('q', '').strip()
    qs = Project.objects.all().order_by('-id')
    if query:
        qs = qs.filter(Q(title__icontains=query))
    paginator = Paginator(qs, 10)
    projects = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'campaigns/project_list.html', {
        'projects': projects, 
        'query': query,
    })

@login_required(login_url='login')
def project_create(request):
    form = ProjectForm(request.POST or None, request.FILES or None) 
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Project created successfully.')
        return redirect('campaigns:project_list')
    return render(request, 'campaigns/project_form.html', {
        'form': form, 'title': 'Add Project',
    })

@login_required(login_url='login')
def project_update(request, pk):
    project = get_object_or_404(Project, pk=pk)
    form = ProjectForm(request.POST or None, request.FILES or None, instance=project)
    
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Project updated successfully.')
        return redirect('campaigns:project_list')
        
    return render(request, 'campaigns/project_form.html', {
        'form': form, 'title': 'Edit Project',
    })

@login_required(login_url='login')
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        project.delete()
        messages.success(request, f'Project "{project.title}" deleted successfully.')
    return redirect('campaigns:project_list')