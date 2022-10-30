import random
import string


def generate_id():
    """
    Generate a random card id of 8 alphanumeric characters
    """
    return "".join(random.choices(string.ascii_letters + string.digits, k=16))


def truncate_text(text: str, max_length: int = 20) -> str:
    """
    Return a truncated version of the text with ellipsis if longer than max_length
    """
    return text[:max_length] + ("..." if len(text) > max_length else "")
