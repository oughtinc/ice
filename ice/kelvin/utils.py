import random
import string


def generate_id():
    """
    Generate a random card id of 8 alphanumeric characters
    """
    return "".join(random.choices(string.ascii_letters + string.digits, k=16))
