from django.urls import path
from . import views

app_name = 'investors'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('create/', views.investor_create, name='investor_create'),
    path('<int:pk>/update/', views.investor_update, name='investor_update'),
    path('<int:pk>/delete/', views.investor_delete, name='investor_delete'),
]