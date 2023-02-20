from structlog.stdlib import get_logger

from ice.nn.bert_t5_t0_ensemble import BERT_T5_T0

log = get_logger()

# https://pypi.org/project/numerizer/ would be a more robust package for this however given the state of peotry it is not worth it
# Should be looked at again in the future


def extract_numbers(text: str) -> list[str]:
    words = text.split()

    set_number_str = {
        "zero",
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten",
        "teen",
        "twenty",
        "thirty",
        "forty",
        "fifty",
        "sixty",
        "seventy",
        "eighty",
        "ninety",
        "hundred",
        "thousand",
        "million",
        "billion",
        "trillion",
        "quadrillion",
        "quintillion",
    }
    number_strings = list(filter(lambda word: word.lower() in set_number_str, words))

    numbers_set = set("0123456789")
    number_strings += list(
        filter(lambda x: set(x).intersection(numbers_set) != set(), words)
    )

    # Remove parentheses
    remove_parentheses = (
        lambda s: s.replace("(", "")
        .replace(")", "")
        .replace("...", "")
        .replace("..", "")
    )
    number_strings = list(map(remove_parentheses, number_strings))

    # Remove "," or "." from the end of the number string
    for i, number in enumerate(number_strings):
        if number[-1] == "," or number[-1] == ".":
            number_strings[i] = number[:-1]

    return number_strings


def classify_example():
    abstract = """In this study we will examine the impact of the use of ..."""
    paragraph = """[..] The adherence rate is 88.2%."""
    numbers = extract_numbers(paragraph)
    category = "adherence"

    for number in numbers:
        classification = BERT_T5_T0(category, abstract, paragraph, number)
        log.info(f"{number}: {classification}")


if __name__ == "__main__":
    classify_example()
