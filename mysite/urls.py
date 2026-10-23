from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core import views as core_views # Inilipat natin sa taas ang import

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # LOGIN/LOGOUT/REGISTER (Idinagdag natin dito para gumana)
    path('login/', core_views.login_view, name='login'),
    path('logout/', core_views.logout_view, name='logout'),
    path('register/', core_views.register_view, name='register'),
    
    # Existing apps
    path('', include('apps.core.urls')), 
    path('users/', include('apps.users.urls')),
    path('info/', include('apps.info.urls')),
    
    # New Crowdfunding apps
    path('campaigns/', include('apps.campaigns.urls')),
    path('investors/', include('apps.investors.urls')),
    path('investments/', include('apps.investments.urls')),
    path('rewards/', include('apps.rewards.urls')),
]

# Para lumabas ang mga pictures (media) sa website
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)