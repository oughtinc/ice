from typing import Optional

from fvalues import F

from ice.recipes.primer.debate.types import *


def initialize_debate(question: Message) -> Debate:
    return [
        ("Question", question),
        ("Alice", "I'm in favor."),
        ("Bob", "I'm against."),
    ]


def render_debate(debate: Debate, self_name: Optional[Name] = None) -> str:
    debate_text = ""
    for speaker, text in debate:
        if speaker == self_name:
            speaker = "You"
        debate_text += F(f'{speaker}: "{text}"\n')
    return debate_text.strip()
