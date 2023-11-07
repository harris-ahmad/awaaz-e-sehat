from django.contrib import admin
from django.urls import path, include 

urlpatterns = [
    # django's admin panel
    path('admin/', admin.site.urls),

    # user management
    path('accounts/', include('django.contrib.auth.urls')),

    # local apps
    path('', include('pages.urls')),
]
