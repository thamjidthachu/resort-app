# Create your views here.

from django.views.generic import ListView
from apps.service.models import Service


class HomeView(ListView):
    template_name = 'home.html'
    context_object_name = 'sevices'

    def get_queryset(self):
        return Service.objects.order_by('-create_time')[:12]
