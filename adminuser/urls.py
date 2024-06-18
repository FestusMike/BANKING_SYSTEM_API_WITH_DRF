from django.urls import path
from .views import AdminUserRUDAPIView, UsersListAPIView

urlpatterns = [
    path("users/<int:id>", AdminUserRUDAPIView.as_view(), name="user-admin-rud"),
    path("users", UsersListAPIView.as_view(), name="users-list"),
]
