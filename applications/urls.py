from django.urls import path

from .views import (
    ApplicationCreateView,
    EmployerApplicationListView,
    EmployerApplicationStatusUpdateView,
)

urlpatterns = [
    path('create/', ApplicationCreateView.as_view(), name='application-create'),
    path('employer/', EmployerApplicationListView.as_view(), name='employer-application-list'),
    path('employer/<int:pk>/status/', EmployerApplicationStatusUpdateView.as_view(), name='employer-application-status-update'),
]
