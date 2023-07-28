from django.urls import path
from . import views

app_name = 'service'
urlpatterns = [
    path('', views.PageList.as_view(), name='list'),
    path('<slug:slug>', views.Details.as_view(), name='details'),
    path('reply', views.replyPost, name='replies'),
]
