from django.urls import path
from .views import TransferAPIView, UserTransactionListView, UserTransactionRetrieveView, StatementOfAccountAPIView

urlpatterns = [
    path("transfer", TransferAPIView.as_view(), name="funds-transfer"),
    path("transactions", UserTransactionListView.as_view(), name="user-transactions"),
    path(
        "transactions/<int:transaction_id>",
        UserTransactionRetrieveView.as_view(),
        name="user-transaction-detail",
    ),
    path(
        "statement", StatementOfAccountAPIView.as_view(), name="statement_of_account"
    ),
]
