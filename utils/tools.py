import random
from django.utils import timezone
from django.db import models
from utils.snowflake import Snowflake

def generate_account_number():
    """Generates a 10-digit account number."""
    current_year_last_two_digits = timezone.now().year % 100
    account_number = [current_year_last_two_digits // 10, current_year_last_two_digits % 10]

    for _ in range(8):  
        random_digit = random.randint(0, 9)
        account_number.append(random_digit)

    random.shuffle(account_number[2:])  

    account_number_str = "".join(map(str, account_number))

    return account_number_str

def generate_transaction_id():
    """Generates a 16-digit transaction id."""
    current_year_last_two_digits = timezone.now().year % 100
    transaction_id = [current_year_last_two_digits // 10, current_year_last_two_digits % 10]

    for _ in range(14):  
        random_digit = random.randint(0, 9)
        transaction_id.append(random_digit)

    random.shuffle(transaction_id[2:])  

    transaction_id_str = "".join(map(str, transaction_id))

    return transaction_id_str


class BaseModel(models.Model):
    """Base model with id attribute for all models requiring a snowflake id"""

    id = models.BigIntegerField(
        primary_key=True,
        default=Snowflake(1, 1).generate_id,
        editable=False,
    )

    class Meta:
        abstract = True
