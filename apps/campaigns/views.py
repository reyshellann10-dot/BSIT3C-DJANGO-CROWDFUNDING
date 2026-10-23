from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import Project
from .forms import ProjectForm
from apps.investments.models import Investment

# --- DASHBOARD ---
@login_required(login_url='login')
def dashboard(request):
    total_projects = Project.objects.count()
    recent_projects = Project.objects.all().order_by('-id')[:5] 
    
    # GET RECENT INVESTMENTS
    recent_investments = Investment.objects.all().order_by('-id')[:5]
    total_investments = Investment.objects.count()

    return render(request, 'campaigns/dashboard.html', {
        'total_projects': total_projects,
        'recent_projects': recent_projects,
        'recent_investments': recent_investments,
        'total_investments': total_investments,
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
        'form': form, 
        'title': 'Add Project',
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
        'form': form, 
        'title': 'Edit Project',
    })


@login_required(login_url='login')
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        project.delete()
        messages.success(request, f'Project "{project.title}" deleted successfully.')
    return redirect('campaigns:project_list')