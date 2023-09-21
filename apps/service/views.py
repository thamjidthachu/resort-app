# Create your views here.
import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormMixin

from apps.authentication.models import User
from resortproject import settings
from .forms import CommentsForm
from .models import Service, Review


class PageList(ListView):
    template_name = 'services/list.html'
    context_object_name = 'resort_services'
    paginate_by = 5

    def get_queryset(self):
        return Service.objects.order_by('-create_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        n = self.get_queryset().count()
        context['left_services'] = self.get_queryset()[n // 2:n]
        context['right_services'] = self.get_queryset()[0:n // 2]
        return context

    def listing(request):
        name = Service.objects.all()
        paginator = Paginator(name, 5)  # Show 5 contacts per page.

        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return render(request, 'list.html', {'page_obj': page_obj})


# Service_Individual
class Details(FormMixin, DetailView):
    template_name = 'services/detail.html'
    form_class = CommentsForm
    model = Service
    context_object_name = 'service'

    def get_context_data(self, **kwargs):
        context = super(Details, self).get_context_data(**kwargs)
        context['related_services'] = Service.objects.all().exclude(slug=self.kwargs['slug']).order_by('-create_time')
        return context


    def get_success_url(self):
        return reverse('service:details', kwargs={'slug': self.kwargs['slug']})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        myform = form.save(commit=False)
        myform.post = self.get_object()
        myform.author = get_object_or_404(User, user_id=self.request.user.id)
        myform.content_type = ContentType.objects.get(app_label='Services', model='services')
        myform.content_object = get_object_or_404(Service, pk=self.object.id)
        myform.save()
        return super(Details, self).form_valid(form)

    def form_invalid(self, form):
        return super(Details, self).form_invalid(form)


def replyPost(request):
    content_obj = ContentType.objects.get(app_label='Services', model='comments')
    obj_id = request.POST['reply_id']
    reply = request.POST['reply']
    auth = get_object_or_404(User, user_id=request.POST['authuser'])
    commenter = get_object_or_404(Review, id=request.POST['reply_id'])
    users = get_object_or_404(User, id=commenter.author.id)
    check = get_object_or_404(User, id=users.user_id)
    email = check.email
    timestamp = datetime.datetime.now(tz=timezone.utc)
    newreply, created = Review.objects.get_or_create(
        content_type=content_obj,
        object_id=obj_id,
        message=reply,
        author=auth,
        comment_time=timestamp
    )

    test = get_object_or_404(Service, id=request.POST['service'])
    slugify = test.slug
    subject = 'Resort Business'
    message = f'Hi {users}, {auth} replied on your Comment "{commenter}" as "{reply}"'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email, ]

    if not created:
        newreply.save()
    send_mail(subject, message, email_from, recipient_list)
    return redirect(reverse('service:datas', args=[slugify]))
