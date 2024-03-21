import random
from datetime import datetime

def primary_key(num_digits):
    """Generates a primary key string with specified number of digits.

    Args:
        num_digits: The desired number of digits in the primary key.

    Returns:
        A string containing the generated primary key.

    Raises:
        ValueError: If the requested number of digits is less than 1.
    """

    if num_digits < 1:
        raise ValueError("Number of digits must be at least 1")

    current_year_last_two_digits = datetime.now().year % 100
    primary_key = [current_year_last_two_digits]

    for _ in range(num_digits - 2):
        random_digit = random.randint(0, 9)
        primary_key.append(random_digit)

    primary_key_str = "".join(map(str, primary_key))

    return primary_key_str
