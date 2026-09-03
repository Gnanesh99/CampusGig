from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import GigForm
from .models import Gig


class HomePageView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['gigs'] = Gig.objects.filter().order_by('-created_at')
        return context


class GigListView(ListView):
    model = Gig
    template_name = 'gigs/gig_list.html'
    context_object_name = 'gigs'


class GigDetailView(DetailView):
    model = Gig
    template_name = 'gigs/gig_detail.html'
    context_object_name = 'gig'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gig = self.object
        user = self.request.user
        context['is_owner'] = user.is_authenticated and gig.poster_id == user.id
        context['has_applied'] = user.is_authenticated and gig.applications.filter(applicant_id=user.id).exists()
        return context


class GigCreateView(LoginRequiredMixin, CreateView):
    model = Gig
    template_name = 'gigs/gig_form.html'
    form_class = GigForm
    success_url = reverse_lazy('gig-list')

    def form_valid(self, form):
        form.instance.poster = self.request.user
        return super().form_valid(form)


class GigUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Gig
    template_name = 'gigs/gig_form.html'
    form_class = GigForm
    success_url = reverse_lazy('gig-list')

    def test_func(self):
        return self.get_object().poster == self.request.user


class GigDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Gig
    template_name = 'gigs/gig_confirm_delete.html'
    success_url = reverse_lazy('gig-list')

    def test_func(self):
        return self.get_object().poster == self.request.user
