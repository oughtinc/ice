from fvalues import F

DEFAULT_QUESTION = "Beth bakes 4x 2 dozen batches of cookies in a week. If these cookies are shared amongst 16 people equally, how many cookies does each person consume?"

DEFAULT_STEPS = [
    "Beth bakes 4x 2 dozen batches of cookies for a total of 4*2 = 8 dozen cookies",
    "There are 12 cookies in a dozen and she makes 8 dozen cookies for a total of 12*8 = 96 cookies",
    "She splits the 96 cookies equally amongst 16 people so they each eat 96/16 = 6 cookies",
    "So, the final answer is 6 cookies per person.",
]


def render_steps(steps: list[str]) -> str:
    return F("\n").join(F(f"{i}. {step}") for (i, step) in enumerate(steps, start=1))
