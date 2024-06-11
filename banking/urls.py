from django.urls import path
from .views import (
                    AccountInfoAPIView,
                    TransferAPIView, 
                    UserTransactionListView, 
                    UserTransactionRetrieveView, 
                    StatementOfAccountPDFView, 
                    TransactionImageView)

urlpatterns = [
    path("account-info", AccountInfoAPIView.as_view(), name="account-info"),
    path("funds-transfer", TransferAPIView.as_view(), name="funds-transfer"),
    path("transactions", UserTransactionListView.as_view(), name="user-transactions"),
    path("transactions/<int:transaction_id>", UserTransactionRetrieveView.as_view(), name="transaction-detail"),
    path("transactions/<int:transaction_id>/image", TransactionImageView.as_view(), name="transaction-image",),
    path("statement-of-account", StatementOfAccountPDFView.as_view(), name="send-account-statement"),
]
