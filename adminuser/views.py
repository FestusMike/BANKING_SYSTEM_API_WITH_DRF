from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from drf_spectacular.utils import extend_schema, OpenApiParameter
from accounts.serializers import UserDetailSerializer

# Create your views here.

User = get_user_model()

@extend_schema(
    description=  """
    This endpoint allows an admin to fetch a list of all the users in the database, in descending order.\n 
    To speed up the database query, a query parameter ('page') can be appended to the url and the value\n 
    can be set to any page number, commonly starting from one.
    """,
    responses={
        200: UserDetailSerializer(many=True),
        401: {"description" : "Unauthorized"},
        500: {"description": "Internal server error"},
    },
    methods=["GET"],
    parameters=[
        OpenApiParameter(name="page", description="Page number", required=False, type=int),
    ],
    )
class UsersListAPIView(generics.ListAPIView):
    """
    This view allows an admin to fetch a list of all the users in the database, in descending order.\n 
    To speed up the database query, a query parameter ('page') can be appended to the url and the value\n 
    can be set to any page number, commonly starting from one.
    """
    
    queryset = User.objects.all().order_by("-date_created")
    permission_classes = [IsAdminUser]
    serializer_class = UserDetailSerializer
    pagination_class = PageNumberPagination

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request, view=self)
        serializer = self.get_serializer(paginated_queryset, many=True)
        response_data = {
            'status' : status.HTTP_200_OK,
            'success' : True,
            'data' : serializer.data
            }
        return paginator.get_paginated_response(response_data)

@extend_schema(
    description= """
    This endpoint authorizes only an admin to perform Read, Update, and Delete operations\n
    on a user, simply by fetching the user's id.
    """,
    responses={
        200: UserDetailSerializer,
        400: {"description": "Bad request"},
        401: {"description": "Unauthorized"},
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    },
    methods=["GET", "PUT", "PATCH", "DELETE"],
)

class AdminUserRUDAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    This view authorizes only an admin to perform Read, Update, and Delete operations\n
    on a user, simply by fetching the user's id.
    """
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsAdminUser]
    parser_classes = [FormParser, MultiPartParser, JSONParser]
    lookup_field = 'id'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        response_data = {
            'status': status.HTTP_200_OK,
            'success' : True,
            'message': 'User retrieved successfully',
            'data': serializer.data
        }
        return Response(response_data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_data = {
            'status': status.HTTP_200_OK,
            'success' : True,
            'message': 'User updated successfully',
            'data': serializer.data
        }
        return Response(response_data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        response_data = {
            'status': status.HTTP_204_NO_CONTENT,
            'success' : True,
            'message': 'User deleted successfully',
        }
        return Response(response_data, status=status.HTTP_204_NO_CONTENT)