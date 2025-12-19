from django.urls import path
from .views import IndexView, HealthCheckView

app_name = 'index'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('healthz/', HealthCheckView.as_view(), name='healthz'),
]
