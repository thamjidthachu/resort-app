from django.urls import path
from .views import HomeView, ServiceListView, ServiceDetailView, ServiceReviewsView, ReviewReplyView, AdvertiseView, FavoriteListCreateView, FavoriteDeleteView

app_name = 'service'
urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('advertisement/', AdvertiseView.as_view(), name='advertise-list'),
    path('list/', ServiceListView.as_view(), name='service-list'),
    path('<slug:slug>/detail/', ServiceDetailView.as_view(), name='service-detail'),
    path('<slug:service_slug>/reviews/', ServiceReviewsView.as_view(), name='service-reviews'),
    path('reviews/<int:comment_id>/reply/', ReviewReplyView.as_view(), name='review-reply'),
    path('favorites/list-create/', FavoriteListCreateView.as_view(), name='favorite-list-create'),
    path('favorites/delete/<int:service_id>/', FavoriteDeleteView.as_view(), name='favorite-delete'),
]
