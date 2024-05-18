from django.urls import path
from .views import (TransferAPIView, 
                    UserTransactionListView, 
                    UserTransactionRetrieveView, 
                    StatementOfAccountPDFView, 
                    TransactionImageView)

urlpatterns = [
    path("transfer", TransferAPIView.as_view(), name="funds-transfer"),
    path("transactions", UserTransactionListView.as_view(), name="user-transactions"),
    path(
        "transactions/<int:transaction_id>",
        UserTransactionRetrieveView.as_view(),
        name="transaction-detail",
    ),
    path(
        "transactions/<int:transaction_id>/image",
        TransactionImageView.as_view(),
        name="transaction-image",
    ),
    path(
        "statement", 
        StatementOfAccountPDFView.as_view(), 
        name="send-account-statement"),
]