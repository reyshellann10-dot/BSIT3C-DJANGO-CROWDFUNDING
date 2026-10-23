from django.urls import path
from . import views

app_name = 'rewards'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('', views.reward_list, name='reward_list'),
]