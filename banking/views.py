from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.template.loader import render_to_string
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from PIL import Image
from .utils import send_attachment_email
from accounts.utils import send_email
from .serializers import TransferSerializer, TransactionSerializer, AccountSerializer, TransactionImageSerializer
from .operations import transfer_funds
from .models import Transaction, Ledger, Account
from .permissions import IsOwnerOfTransaction
from .utils import generate_ledger_pdf
import io
import os
import base64
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class AccountInfoAPIView(generics.GenericAPIView):
    """
    This view handles provides the details of a verified user based on a valid account number\n 
    provided in the query parameter. An explicit explanation is that a user has the account number\n
    of another user but they want to verify their details. This view comes in handy for such use case.
    """    
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
    description= """
    This endpoint handles provides the details of a verified user based on a valid account number\n 
    provided in the query parameter. An explicit explanation is that a user has the account number\n
    of another user but they want to verify their details. This endpoint comes in handy for such use case.
    """,
    parameters=[
        OpenApiParameter(name="account_number", description="Account Number", required=True, type=str),
    ],
    responses={
        200: AccountSerializer,
        400: {"description": "Account Number is Required"},
        404: {"description": "Invalid Account Number"},
    },
    methods=["GET"]
    )
    def get(self, request, *args, **kwargs):
        account_number = request.query_params.get('account_number')
        if not account_number:
             return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "Success": False,
                    "message": "Account Number is Required.",
                },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        try:
            account = Account.objects.get(account_number=account_number)
        except Account.DoesNotExist:
            return Response(
                {
                    "status": status.HTTP_404_NOT_FOUND,
                    "Success": False,
                    "message": "Invalid Account Number.",
                },
                    status=status.HTTP_404_NOT_FOUND,
                )
        serializer = self.get_serializer(account)
        return Response(
                {
                    "status": status.HTTP_200_OK,
                    "Success": True,
                    "message": serializer.data,
                },
                    status=status.HTTP_200_OK,
                )


class TransferAPIView(generics.GenericAPIView):
    """
    This view handles funds transfer between two verified users. A user sends funds to a fellow user\n
    and their accounts both get debited and credited immediately. The two users involved in the transaction also get\n
    email alerts immediately after successful transaction.
    """
    serializer_class = TransferSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
    description="""
    This endpoint handles funds transfer between two verified users. A user sends funds to a fellow user\n
    and their accounts both get debited and credited immediately. The two users involved in the transaction also receive\n
    email alerts immediately after successful transaction.
    """,
    request=TransferSerializer,
    responses={
        200: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
                "transaction_id": {"type": "string"},
            },
        },
        400: {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "Success": {"type": "boolean"},
                "message": {"type": "string"},
            },
        },
       
        },
    methods=["POST"],
)    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from_user = request.user

        if not check_password(serializer.validated_data["pin"], from_user.pin):
            response_data = {
                "status" : status.HTTP_400_BAD_REQUEST,
                "success" : False,
                "error": "Incorrect PIN"
                } 
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        try:
            debit_transaction, credit_transaction = transfer_funds(
                from_user.id,
                serializer.validated_data["to_account_number"],
                serializer.validated_data["amount"],
                serializer.validated_data.get("description", ""),
            )

            sender_name = debit_transaction.from_account.user.full_name
            sender_email = debit_transaction.from_account.user.email
            sender_balance = debit_transaction.from_account.current_balance
            recipient_name = credit_transaction.to_account.user.full_name
            recipient_email = credit_transaction.to_account.user.email
            recipient_account_number = credit_transaction.to_account.account_number
            recipient_balance = credit_transaction.to_account.current_balance

            local_tz = timezone.get_current_timezone()
            timestamp = (
                credit_transaction.timestamp
                if credit_transaction
                else debit_transaction.timestamp
            )
            local_timestamp = timezone.localtime(timestamp, local_tz)

            date = local_timestamp.strftime("%A, %d %B, %Y")
            time = local_timestamp.strftime("%H:%M:%S")

            credit_context =  {
                    "recipient_name": recipient_name,
                    "sender_name": sender_name,
                    "amount": serializer.validated_data["amount"],
                    "description": serializer.validated_data.get("description", ""),
                    "date": date,
                    "time": time,
                    "current_balance": recipient_balance,
                }
            debit_context = {
                    "recipient_name": recipient_name,
                    "sender_name": sender_name,
                    "recipient_account_number": recipient_account_number,
                    "amount": serializer.validated_data["amount"],
                    "description": serializer.validated_data.get("description", ""),
                    "date": date,
                    "time": time,
                    "current_balance": sender_balance,
                }

            credit_message = render_to_string('credit_alert_email.html', credit_context)
            debit_message = render_to_string('debit_alert_email.html', debit_context)
            subject = "Transaction Alert!"

            if debit_transaction:
                send_email(
                    to=[{"email": sender_email, "name": sender_name}],
                    subject=subject,
                    html_content=debit_message,
                    sender={
                        "name": "Longman Technologies",
                        "email": os.getenv("EMAIL_SENDER"),
                    },
                    reply_to={"email": os.getenv("REPLY_TO_EMAIL")},
                )

            if credit_transaction:
                send_email(
                    to=[{"email": recipient_email, "name": recipient_name}],
                    subject=subject,
                    html_content=credit_message,
                    sender={
                        "name": "Longman Technologies",
                        "email": os.getenv("EMAIL_SENDER"),
                    },
                    reply_to={"email": os.getenv("REPLY_TO_EMAIL")},
                )

            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "Success": True,
                    "message": f"Your transfer of {serializer.validated_data['amount']} to {recipient_name} is successful.",
                    "transaction_id": debit_transaction.transaction_id,
                }
            )

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    description="""
    This endpoint allows a user to fetch all the transactions they are invloved in.\n
    To speed up database query, a query parameter('page') may be appended to the url\n
    and the value can be any digit, commonly starting from one.
    """,
    responses={
        200: TransactionSerializer(many=True),
        500: {"description": "Internal Server Error"},
    },
    methods=["GET"],
    parameters=[
        OpenApiParameter(
            name="page", description="Page number", required=False, type=int
        ),
    ],
)
class UserTransactionListView(generics.ListAPIView):
    """
    This view allows a user to fetch all the transactions they are invloved in.\n
    To speed up database query, a query parameter('page') may be appended to the url\n
    and the value can be any digit, commonly starting from one.
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsOwnerOfTransaction]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        user = self.request.user
        user_accounts = user.accounts.all()

        debit_transactions = Transaction.objects.filter(
            from_account__in=user_accounts, transaction_type="DEBIT"
        )

        credit_transactions = Transaction.objects.filter(
            to_account__in=user_accounts, transaction_type="CREDIT"
        )

        transactions = debit_transactions | credit_transactions
        return transactions.order_by("-timestamp")

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()

            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(queryset, request, view=self)
            
            serializer = self.get_serializer(paginated_queryset, many=True)
            response_data = {
                "status": status.HTTP_200_OK,
                "success": True,
                "data": serializer.data
            }
            return paginator.get_paginated_response(response_data)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return Response(
                {
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "success": False,
                    "message": "An error occurred while processing your request."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserTransactionRetrieveView(generics.RetrieveAPIView):
    """
    This view allows a user to fetch a particular transaction they are involved in\n 
    by appending the transaction id to the url as a parameter. 
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsOwnerOfTransaction]
    queryset = Transaction.objects.all()
    lookup_field = "transaction_id"


class TransactionImageView(generics.RetrieveAPIView):
    """
    This view allows a user to get the image(jpeg format) of a transaction they are\n
    involved in by simply appending the transaction id to the url as a parameter.
    """
    serializer_class = TransactionImageSerializer
    permission_classes = [IsAuthenticated, IsOwnerOfTransaction]
    queryset = Transaction.objects.all()
    lookup_field = "transaction_id"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        image = self.generate_image(instance)
        return HttpResponse(image, content_type="image/jpeg")

    def generate_image(self, instance):
        img = Image.new("RGB", (100, 50), color="white")
        img_byte_array = io.BytesIO()
        img.save(img_byte_array, format="JPEG")
        return img_byte_array.getvalue()


class StatementOfAccountPDFView(generics.GenericAPIView):
    """
    This view gives room for a user to generate an account statement which will be immediately\n
    sent to their email. A user can generate account records for all their transactions or for\n
    transactions within a specific timeframe. To generate transaction records for a specific timeframe,\n
    a user can append two query parameters to the url('start_date', 'end_date') with the two parameters\n
    taking date values in YYYY-MM-DD format.\n 
    Example: api/v1/statement-of-account?start_date=2024-06-11&end_date=2024-06-11\n
    To generate account statement for all transactions, no query parameter is needed.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
    description="""
    This endpoint gives room for a user to generate an account statement which will be immediately\n
    sent to their email. A user can generate account records for all their transactions or for\n
    transactions within a specific timeframe. To generate transaction records for a specific timeframe,\n
    a user can append two query parameters to the url('start_date', 'end_date') with the two parameters\n
    taking date values in YYYY-MM-DD format.\n 
    Example: api/v1/statement-of-account?start_date=2024-06-11&end_date=2024-06-11\n
    To generate account statement for all transactions, no query parameter is needed.
    """,
    parameters=[
        OpenApiParameter(name="start_date", description="Start date", required=False, type=str),
        OpenApiParameter(name="end_date", description="End date", required=False, type=str),
    ],
    responses={
        200: {"description": "Statement of account sent successfully"},
        400: {"description": "Invalid date format provided"},
    },
    methods=["GET"]
    )    
    def get(self, request):
        user = request.user
        accounts = user.accounts.all()
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if start_date and end_date:
            try:
                start_date = make_aware(parse_datetime(start_date + "T00:00:00"))
                end_date = make_aware(parse_datetime(end_date + "T23:59:59"))
                ledger_entries = Ledger.objects.filter(
                    account__in=accounts,
                    transaction__timestamp__range=[start_date, end_date]
                ).select_related("transaction").order_by("-transaction__timestamp")
                start_date_str = start_date.strftime("%Y-%m-%d")
                end_date_str = end_date.strftime("%Y-%m-%d")
            except ValueError:
                return Response({"error": "Invalid date format provided."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            ledger_entries = Ledger.objects.filter(account__in=accounts).select_related("transaction").order_by("-transaction__timestamp")
            start_date_str = "the beginning"
            end_date_str = "now"

        pdf = generate_ledger_pdf(ledger_entries, user, start_date, end_date)
        pdf_base64 = base64.b64encode(pdf).decode("utf-8")

        attachment = [{
            "content": pdf_base64,
            "name": f"{user.full_name}_statement_of_account_{timezone.localtime().strftime('%Y-%m-%d_%H-%M-%S')}.pdf",
            "type": "application/pdf",
        }]
        context =  {
                "user": user,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "company_name": "Longman Technologies",
            } 
        html_content = render_to_string("statement_of_account.html", context)

        to = [{"email": user.email, "name": user.full_name}]
        reply_to = {"email": os.getenv("REPLY_TO_EMAIL")}
        sender = {
            "name": "Longman Technologies",
            "email": os.getenv("EMAIL_SENDER"),
        }
        subject = "Your Statement of Account from Longman Technologies"

        send_attachment_email(to, reply_to, html_content, sender, subject, attachment)
        response_data = {
            "status" : status.HTTP_200_OK,
            "success" : True,
            "message": "Requested account statement on its way to your registered email. Kindly check your inbox.",
            }
        return Response(response_data, status=status.HTTP_200_OK)
