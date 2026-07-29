from django.urls import path

from .views import (
    GigCreateView,
    GigDeleteView,
    GigDetailView,
    GigListView,
    GigUpdateView,
)

urlpatterns = [
    path('', GigListView.as_view(), name='gig-list'),
    path('new/', GigCreateView.as_view(), name='gig-create'),
    path('<int:pk>/', GigDetailView.as_view(), name='gig-detail'),
    path('<int:pk>/edit/', GigUpdateView.as_view(), name='gig-update'),
    path('<int:pk>/delete/', GigDeleteView.as_view(), name='gig-delete'),
]
