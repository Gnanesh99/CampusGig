from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import ModelForm
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .models import Application


class ApplicationCreateView(LoginRequiredMixin, CreateView):
    model = Application
    fields = ['gig', 'cover_letter']
    template_name = 'applications/application_form.html'
    success_url = reverse_lazy('gig-list')

    def form_valid(self, form):
        gig = form.cleaned_data.get('gig')
        user = self.request.user

        if gig and gig.poster == user:
            form.add_error('gig', 'You cannot apply to your own gig.')
            return self.form_invalid(form)

        if Application.objects.filter(gig=gig, applicant=user).exists():
            form.add_error('gig', 'You have already applied to this gig.')
            return self.form_invalid(form)
        form.instance.applicant = user
        return super().form_valid(form)


class EmployerApplicationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Application
    template_name = 'applications/application_list.html'
    context_object_name = 'applications'

    def get_queryset(self):
        return Application.objects.filter(gig__poster=self.request.user).select_related('gig', 'applicant')

    def test_func(self):
        return True


class EmployerApplicationStatusUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Application
    fields = ['status']
    template_name = 'applications/application_status_form.html'
    success_url = reverse_lazy('employer-application-list')

    def get_queryset(self):
        return Application.objects.filter(gig__poster=self.request.user)

    def test_func(self):
        return self.get_object().gig.poster == self.request.user
