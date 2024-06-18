from django.urls import path
from .views import CustomerMessageAPIView, UserMessagesAPIView, UserMessageDetailAPIView

urlpatterns = [
   path("user/messaging", CustomerMessageAPIView.as_view(), name="customer-message"),
    path('user/messages', UserMessagesAPIView.as_view(), name='user-messages'),
    path('user/messages/<str:reference_id>', UserMessageDetailAPIView.as_view(), name='user-message-detail'),
]