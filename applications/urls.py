from django.urls import path

from .views import (
    ApplicationCreateView,
    EmployerApplicationListView,
    EmployerApplicationStatusUpdateView,
    StudentDashboardView,
    StudentAssignmentListView,
    StudentAssignmentStartView,
    StudentAssignmentSubmitView,
    EmployerDashboardView,
    EmployerAssignmentListView,
    EmployerAssignmentReviewView,
    EmployerAssignmentRejectView,
    EmployerAssignmentAcceptView,
)

urlpatterns = [
    path('create/', ApplicationCreateView.as_view(), name='application-create'),
    path('dashboard/', StudentDashboardView.as_view(), name='student-dashboard'),
    path('employer/', EmployerApplicationListView.as_view(), name='employer-application-list'),
    path('employer/dashboard/', EmployerDashboardView.as_view(), name='employer-dashboard'),
    path('employer/<int:pk>/status/', EmployerApplicationStatusUpdateView.as_view(), name='employer-application-status-update'),
    # Student assignment routes
    path('assignments/', StudentAssignmentListView.as_view(), name='student-assignment-list'),
    path('assignments/<int:pk>/start/', StudentAssignmentStartView.as_view(), name='student-assignment-start'),
    path('assignments/<int:pk>/submit/', StudentAssignmentSubmitView.as_view(), name='student-assignment-submit'),
    # Employer assignment routes
    path('employer/assignments/', EmployerAssignmentListView.as_view(), name='employer-assignment-list'),
    path('employer/assignments/<int:pk>/review/', EmployerAssignmentReviewView.as_view(), name='employer-assignment-review'),
    path('employer/assignments/<int:pk>/reject/', EmployerAssignmentRejectView.as_view(), name='employer-assignment-reject'),
    path('employer/assignments/<int:pk>/accept/', EmployerAssignmentAcceptView.as_view(), name='employer-assignment-accept'),
]
