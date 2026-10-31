from django.urls import path
from . import views

urlpatterns = [
    # Public landing page
    path('', views.home, name='home'),
]
