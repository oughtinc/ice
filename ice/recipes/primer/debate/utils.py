from ice.recipes.primer.debate.types import *


def initialize_debate(question: Message, agent_names: tuple[Name, Name] = ("Alice", "Bob")) -> Debate:
    return [
        ("Question", question),
        (agent_names[0], "I'm in favor."),
        (agent_names[1], "I'm against."),
    ]


def render_debate(debate: Debate, self_name: Name | None = None) -> str:
    debate_text = ""
    for speaker, text in debate:
        if speaker == self_name:
            speaker = "You"
        debate_text += f'{speaker}: "{text}"\n'
    return debate_text.strip()
