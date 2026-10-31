from django.urls import path
from . import views

app_name = 'investments'

urlpatterns = [
    path('',                          views.investment_list,   name='investment_list'),
    path('portfolio/',                views.my_portfolio,      name='my_portfolio'),
    path('invest/<int:project_pk>/',  views.invest_now,        name='invest_now'),
    path('create/',                   views.investment_create, name='investment_create'),
    path('<int:pk>/update/',          views.investment_update, name='investment_update'),
    path('<int:pk>/delete/',          views.investment_delete, name='investment_delete'),
]
