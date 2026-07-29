from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import GigForm
from .models import Gig


class GigListView(ListView):
    model = Gig
    template_name = 'gigs/gig_list.html'
    context_object_name = 'gigs'


class GigDetailView(DetailView):
    model = Gig
    template_name = 'gigs/gig_detail.html'
    context_object_name = 'gig'


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
