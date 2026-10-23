from django.urls import path
from . import views

app_name = 'investments'

urlpatterns = [
    path('', views.investment_list, name='investment_list'),
    # IDINAGDAG NATIN ITO:
    path('create/', views.investment_create, name='investment_create'),
    path('<int:pk>/update/', views.investment_update, name='investment_update'),
    path('<int:pk>/delete/', views.investment_delete, name='investment_delete'),
]