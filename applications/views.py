from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import CreateView, ListView, TemplateView, UpdateView, View

from .models import Application, Assignment
from gigs.models import Gig


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

    def form_valid(self, form):
        response = super().form_valid(form)
        application = self.object

        if application.status == 'hired' and not Assignment.objects.filter(application=application).exists():
            Assignment.objects.create(
                application=application,
                employer=application.gig.poster,
                student=application.applicant,
                status='Assigned',
                hired_at=timezone.now(),
            )

        return response


class StudentDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'applications/student_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['applications'] = Application.objects.filter(applicant=user).select_related('gig')
        context['assignments'] = Assignment.objects.filter(student=user).select_related('application__gig', 'employer')
        return context


class StudentAssignmentListView(LoginRequiredMixin, ListView):
    model = Assignment
    template_name = 'applications/student_assignment_list.html'
    context_object_name = 'assignments'

    def get_queryset(self):
        return Assignment.objects.filter(
            student=self.request.user
        ).select_related('application__gig', 'employer')


class StudentAssignmentStartView(LoginRequiredMixin, View):
    """Transition Assigned → In Progress. Only the assigned student may do this."""

    def post(self, request, pk, *args, **kwargs):
        assignment = get_object_or_404(Assignment, pk=pk)

        if assignment.student != request.user:
            return HttpResponseForbidden('You are not authorised to start this assignment.')

        if assignment.status != 'Assigned':
            return redirect('student-assignment-list')

        assignment.status = 'In Progress'
        assignment.save(update_fields=['status'])
        return redirect('student-assignment-list')


class StudentAssignmentSubmitView(LoginRequiredMixin, View):
    """Allow the student to submit their work. Transition In Progress → Submitted."""

    def get(self, request, pk, *args, **kwargs):
        assignment = get_object_or_404(Assignment, pk=pk)

        if assignment.student != request.user:
            return HttpResponseForbidden('You are not authorised to submit this assignment.')

        if assignment.status != 'In Progress':
            return redirect('student-assignment-list')

        return render(request, 'applications/student_assignment_submit.html', {'assignment': assignment})

    def post(self, request, pk, *args, **kwargs):
        assignment = get_object_or_404(Assignment, pk=pk)

        if assignment.student != request.user:
            return HttpResponseForbidden('You are not authorised to submit this assignment.')

        if assignment.status != 'In Progress':
            return redirect('student-assignment-list')

        submission_text = request.POST.get('submission_text', '').strip()
        submission_file = request.FILES.get('submission_file')

        if not submission_text and not submission_file:
            error = 'Please provide either submission text or a file.'
            return render(request, 'applications/student_assignment_submit.html', {
                'assignment': assignment,
                'error': error,
            })

        if submission_text:
            assignment.submission_text = submission_text
        if submission_file:
            assignment.submission_file = submission_file

        assignment.status = 'Submitted'
        assignment.save(update_fields=['submission_text', 'submission_file', 'status'])
        return redirect('student-assignment-list')


# ---------------------------------------------------------------------------
# Employer Assignment views
# ---------------------------------------------------------------------------

class EmployerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'applications/employer_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['posted_gigs'] = Gig.objects.filter(poster=user).select_related('category')
        context['applications_received'] = Application.objects.filter(gig__poster=user).select_related('gig', 'applicant')
        context['assignments'] = Assignment.objects.filter(employer=user).select_related('application__gig', 'student')
        return context


class EmployerAssignmentListView(LoginRequiredMixin, ListView):
    """Lists all assignments where the logged-in user is the employer."""
    model = Assignment
    template_name = 'applications/employer_assignment_list.html'
    context_object_name = 'assignments'

    def get_queryset(self):
        return Assignment.objects.filter(
            employer=self.request.user
        ).select_related('application__gig', 'student')


class EmployerAssignmentReviewView(LoginRequiredMixin, View):
    """Display a Submitted assignment so the employer can accept or reject it."""

    def get(self, request, pk, *args, **kwargs):
        assignment = get_object_or_404(Assignment, pk=pk)

        if assignment.employer != request.user:
            return HttpResponseForbidden('You are not authorised to review this assignment.')

        return render(request, 'applications/employer_assignment_review.html', {
            'assignment': assignment,
        })


class EmployerAssignmentRejectView(LoginRequiredMixin, View):
    """POST-only. Submitted → In Progress, saves employer_feedback."""

    def post(self, request, pk, *args, **kwargs):
        assignment = get_object_or_404(Assignment, pk=pk)

        if assignment.employer != request.user:
            return HttpResponseForbidden('You are not authorised to reject this assignment.')

        if assignment.status != 'Submitted':
            return redirect('employer-assignment-list')

        feedback = request.POST.get('employer_feedback', '').strip()
        assignment.employer_feedback = feedback
        assignment.status = 'In Progress'
        assignment.save(update_fields=['employer_feedback', 'status'])
        return redirect('employer-assignment-list')


class EmployerAssignmentAcceptView(LoginRequiredMixin, View):
    """POST-only. Validates Submitted status, then redirects to payment checkout."""

    def post(self, request, pk, *args, **kwargs):
        assignment = get_object_or_404(Assignment, pk=pk)

        if assignment.employer != request.user:
            return HttpResponseForbidden('You are not authorised to accept this assignment.')

        if assignment.status != 'Submitted':
            return redirect('employer-assignment-list')

        # Retrieve the linked Payment (created automatically when Assignment was created).
        payment = getattr(assignment, 'payment', None)
        if payment is None:
            return HttpResponseForbidden('No payment record found for this assignment.')

        # Redirect into the existing Razorpay checkout flow.
        # Assignment status stays Submitted; Completed is set after successful payment.
        return redirect(reverse('payments:checkout', kwargs={'pk': payment.pk}))
