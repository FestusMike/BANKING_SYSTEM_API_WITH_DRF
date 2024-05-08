from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.serializers import BaseSerializer
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.template.loader import render_to_string
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from PIL import Image
from .utils import send_attachment_email
from accounts.utils import send_email
from .serializers import TransferSerializer, TransactionSerializer
from .operations import transfer_funds
from .models import Transaction, Ledger
from .permissions import IsOwnerOfTransaction
from .utils import generate_ledger_pdf
import io
import os
import base64


User = get_user_model()


class TransferAPIView(generics.GenericAPIView):
    serializer_class = TransferSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        from_user = request.user

        if not check_password(data["pin"], from_user.pin):
            return Response(
                {"error": "Incorrect PIN"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            debit_transaction, credit_transaction = transfer_funds(
                from_user.id,
                data["to_account_number"],
                data["amount"],
                data.get("description", ""),
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

            subject = "Transaction Alert!"
            credit_template = "credit_alert_email.html"
            debit_template = "debit_alert_email.html"

            credit_message = render_to_string(
                credit_template,
                {
                    "recipient_name": recipient_name,
                    "sender_name": sender_name,
                    "amount": data["amount"],
                    "description": data.get("description", ""),
                    "date": date,
                    "time": time,
                    "current_balance": recipient_balance,
                },
            )

            debit_message = render_to_string(
                debit_template,
                {
                    "recipient_name": recipient_name,
                    "sender_name": sender_name,
                    "recipient_account_number": recipient_account_number,
                    "amount": data["amount"],
                    "description": data.get("description", ""),
                    "date": date,
                    "time": time,
                    "current_balance": sender_balance,
                },
            )

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
                    "message": f"Your transfer of {data['amount']} to {recipient_name} is successful.",
                    "transaction_id": debit_transaction.transaction_id,
                }
            )

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserTransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsOwnerOfTransaction]

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
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        response_data = {
            "total": f"{queryset.count()} objects retrieved",
            "data": serializer.data
        }
        return Response(response_data, status=status.HTTP_200_OK)


class UserTransactionRetrieveView(generics.RetrieveAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsOwnerOfTransaction]
    queryset = Transaction.objects.all()
    lookup_field = "transaction_id"


class TransactionImageView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOfTransaction]
    queryset = Transaction.objects.all()
    lookup_field = "transaction_id"

    def get_serializer_class(self):
        if getattr(self, "swagger_fake_view", False):
            return BaseSerializer
        return None

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        image = self.generate_image(instance)
        return HttpResponse(image, content_type="image/jpeg")

    def generate_image(self, transaction):
        img = Image.new("RGB", (100, 50), color="white")
        img_byte_array = io.BytesIO()
        img.save(img_byte_array, format="JPEG")
        return img_byte_array.getvalue()


class TransactionPdfView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOfTransaction]
    queryset = Transaction.objects.all()
    lookup_field = "transaction_id"

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return BaseSerializer
        return None

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        pdf = self.generate_pdf(instance)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            'attachment; filename=f"{self.request.user.full_name}_{instance.transaction_id}.pdf"'
        )
        return response

    def generate_pdf(self, transaction):
        pdf_byte_array = io.BytesIO()
        doc = SimpleDocTemplate(pdf_byte_array, pagesize=letter)

        transaction_id = transaction.transaction_id
        timestamp = transaction.timestamp
        amount = transaction.amount
        description = transaction.description
        from_account = transaction.from_account
        to_account = transaction.to_account

        data = [
            ["Transaction ID:", transaction_id],
            ["Timestamp:", timestamp.strftime("%Y-%m-%d %H:%M:%S")],
            ["Amount:", amount],
            ["Description:", description],
            [
                "Sender:",
                "{} ({})".format(
                    (
                        "You | "
                        if self.request.user == from_account.user
                        else to_account.user.full_name
                    ),
                    (
                        from_account.account_number
                        if self.request.user == from_account.user
                        else to_account.account_number
                    ),
                ),
            ],
            [
                "Recipient:",
                "{} ({})".format(
                    (
                        "You | "
                        if self.request.user == to_account.user
                        else from_account.user.full_name
                    ),
                    (
                        to_account.account_number
                        if self.request.user == to_account.user
                        else from_account.account_number
                    ),
                ),
            ],
        ]
        table = Table(data)
        style = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Courier-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
        table.setStyle(style)
        doc.build([table])
        return pdf_byte_array.getvalue()


class StatementOfAccountPDFView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return BaseSerializer
        return None
    
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

        html_content = render_to_string(
            "statement_of_account.html",
            {
                "user": user,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "company_name": "Longman Technologies",
            }
        )

        to = [{"email": user.email, "name": user.full_name}]
        reply_to = {"email": os.getenv("REPLY_TO_EMAIL")}
        sender = {
            "name": "Longman Technologies",
            "email": os.getenv("EMAIL_SENDER"),
        }
        subject = "Your Statement of Account from Longman Technologies"

        send_attachment_email(to, reply_to, html_content, sender, subject, attachment)

        return Response(
            {"message": "Ledger PDF sent to your email."}, status=status.HTTP_200_OK
        )
