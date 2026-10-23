from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import RewardForm
from .models import Reward


@login_required(login_url='login')
def reward_list(request):
    qs = Reward.objects.all().order_by('-created_at')
    paginator = Paginator(qs, 10)
    rewards = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'crowdfunding/reward_list.html', {
        'rewards': rewards,
    })


@login_required(login_url='login')
def reward_create(request):
    form = RewardForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        reward = form.save()
        messages.success(request, f'Reward "{reward.name}" created.')
        return redirect('crowdfunding:reward_list')
    return render(request, 'crowdfunding/reward_form.html', {
        'form': form, 'title': 'Add Reward',
    })


@login_required(login_url='login')
def reward_update(request, pk):
    reward = get_object_or_404(Reward, pk=pk)
    form = RewardForm(request.POST or None, instance=reward)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Reward "{reward.name}" updated.')
        return redirect('crowdfunding:reward_list')
    return render(request, 'crowdfunding/reward_form.html', {
        'form': form, 'title': 'Edit Reward',
    })


@login_required(login_url='login')
def reward_delete(request, pk):
    reward = get_object_or_404(Reward, pk=pk)
    if request.method == 'POST':
        messages.success(request, f'Reward "{reward.name}" deleted.')
        reward.delete()
    return redirect('crowdfunding:reward_list')

    from django.shortcuts import render

def dashboard(request):
    return render(request, 'rewards/dashboard.html', {})