from django.contrib import admin
from django.urls import include, path

from gigs.views import HomePageView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('admin/', admin.site.urls),
    path('gigs/', include('gigs.urls')),
    path('applications/', include('applications.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]
