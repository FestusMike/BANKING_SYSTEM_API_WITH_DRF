from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.pagination import PageNumberPagination
from .models import CustomerMessage, Picture
from .serializers import CustomerMessageSerializer

# Create your views here.


class CustomerMessageAPIView(generics.GenericAPIView):
    """
    This view enables a user to contact Longman technologies directly. Here, a user is mandated to send\n 
    a message alongside the request body and they can also decide to send images to corroborate their concern.\n
    A user can send more than one picture alongside the message, which will be converted to a list\n 
    before being uploaded to the DB. Upon successfully sending the message, the admin will be alerted and the concern\n
    will be taken up.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerMessageSerializer
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        description = """
    This endpoint enables a user to contact Longman technologies directly. Here, a user is mandated to send\n 
    a message alongside the request body and they can also decide to send images to corroborate their concern.\n
    A user can send more than one picture alongside the message, which will be converted to a list\n 
    before being uploaded to the DB. Upon successfully sending the message, the admin will be alerted and the concern\n
    will be taken up
    """,
        request=CustomerMessageSerializer,
        responses={
            201: CustomerMessageSerializer,
            400: {"description": "Bad Request"},
            401: {"description": "Unauthorized"},
            500: {"description": "Internal Server Error"},
        },
        parameters=[
            OpenApiParameter(
                name="image_files",
                type={"type": "array", "items": {"type": "string", "format": "binary"}},
                location=OpenApiParameter.QUERY,
                required=False,
                description="List of images to upload",
            )
        ],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user

        message = CustomerMessage.objects.create(
            user=user,
            message=serializer.validated_data["message"],
        )

        image_files = request.FILES.getlist("image_files")

        if image_files:
            pictures = [Picture.objects.create(image=image) for image in image_files]
            message.pictures.set(pictures)

        response_data = {
            "status": status.HTTP_201_CREATED,
            "Success": True,
            "message": "Your message has been received. You'll receive a response from our customer care representative shortly.",
            "data": CustomerMessageSerializer(message).data,
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

@extend_schema(
    description = """
    This endpoint allows a user to view all the messages they have sent to Longman Technologies
    """,
    responses={
        200: CustomerMessageSerializer(many=True),
        401: {"description": "Unauthorized"},
        500: {"description": "Internal Server Error"},
    },
    parameters=[
        OpenApiParameter(name="page", description="Page number", required=False, type=int),
    ],
    )
class UserMessagesAPIView(generics.ListAPIView):
    """This view allows a user to view all the messages they have sent to Longman Technologies"""
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerMessageSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        user = self.request.user
        return CustomerMessage.objects.filter(user=user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request, view=self)
        serializer = self.get_serializer(paginated_queryset, many=True)
        response_data = {
            "status": status.HTTP_200_OK,
            "success": True,
            "data": serializer.data,
        }
        return paginator.get_paginated_response(response_data)


class UserMessageDetailAPIView(generics.RetrieveAPIView):
    """This view allows a user to fetch a message sent by them by the message's reference_id"""
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerMessageSerializer
    lookup_field = "reference_id"

    def get_queryset(self):
        user = self.request.user
        return CustomerMessage.objects.filter(user=user)
