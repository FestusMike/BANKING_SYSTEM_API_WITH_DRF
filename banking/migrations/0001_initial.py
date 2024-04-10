# Generated by Django 5.0.2 on 2024-04-10 10:31

import django.db.models.deletion
import utils.snowflake
import utils.tools
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Account",
            fields=[
                (
                    "account_number",
                    models.BigIntegerField(
                        default=utils.tools.generate_account_number,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                (
                    "account_type",
                    models.CharField(
                        choices=[
                            ("SAVINGS", "Savings"),
                            ("CURRENT", "Current"),
                            ("FIXED DEPOSIT", "Fixed Deposit"),
                        ],
                        default="SAVINGS",
                        max_length=30,
                    ),
                ),
                (
                    "current_balance",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                ("date_created", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="accounts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "Accounts",
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Transaction",
            fields=[
                (
                    "transaction_id",
                    models.BigIntegerField(
                        default=utils.tools.generate_transaction_id,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                (
                    "transaction_type",
                    models.CharField(
                        choices=[("DEBIT", "Debit"), ("CREDIT", "Credit")],
                        default="DEBIT",
                        max_length=20,
                    ),
                ),
                (
                    "transaction_mode",
                    models.CharField(
                        choices=[
                            ("MOBILE APP TRANSFER", "Mobile App Transfer"),
                            ("USSD TRANSFER", "Ussd Transfer"),
                        ],
                        default="MOBILE APP TRANSFER",
                        max_length=50,
                    ),
                ),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "description",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "from_account",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="outgoing_transactions",
                        to="banking.account",
                    ),
                ),
                (
                    "to_account",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="incoming_transactions",
                        to="banking.account",
                    ),
                ),
            ],
            options={
                "db_table": "Transactions",
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Ledger",
            fields=[
                (
                    "id",
                    models.BigIntegerField(
                        default=utils.snowflake.Snowflake.generate_id,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "balance_after_transaction",
                    models.DecimalField(decimal_places=2, max_digits=12),
                ),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ledger_entries",
                        to="banking.account",
                    ),
                ),
                (
                    "transaction",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ledger_entries",
                        to="banking.transaction",
                    ),
                ),
            ],
            options={
                "db_table": "Ledger",
                "abstract": False,
            },
        ),
    ]
