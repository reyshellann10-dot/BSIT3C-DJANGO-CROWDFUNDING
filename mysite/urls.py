from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core import views as core_views

urlpatterns = [
    # Django admin panel — separate from the public site
    path('admin/', admin.site.urls),

    # Public landing page
    path('', core_views.home, name='home'),

    # Public info pages
    path('how-it-works/', core_views.how_it_works, name='how_it_works'),
    path('features/', core_views.features, name='features'),
    path('roles/',    core_views.roles,    name='roles'),

    # Auth
    path('login/',       core_views.login_view,       name='login'),
    path('logout/',      core_views.logout_view,      name='logout'),
    path('register/',    core_views.register_view,    name='register'),
    path('admin-login/', core_views.admin_login_view, name='admin_login'),

    # App modules
    path('users/',       include('apps.users.urls')),
    path('info/',        include('apps.info.urls')),
    path('campaigns/',   include('apps.campaigns.urls')),
    path('investors/',   include('apps.investors.urls')),
    path('investments/', include('apps.investments.urls')),
    path('rewards/',     include('apps.rewards.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
