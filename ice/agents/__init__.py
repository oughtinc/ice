from .approval import ApprovalAgent  # noqa: F401
from .augmented import AugmentedAgent  # noqa: F401
from .base import Agent  # noqa: F401
from .fake import FakeAgent  # noqa: F401
from .human import HumanAgent  # noqa: F401
from .openai import OpenAIAgent  # noqa: F401
from .openai_reasoning import OpenAIReasoningAgent  # noqa: F401
from .ought_inference import OughtInferenceAgent  # noqa: F401
from .squad import SquadAgent  # noqa: F401


def get_agents():
    return [
        ApprovalAgent,
        AugmentedAgent,
        FakeAgent,
        HumanAgent,
        OpenAIAgent,
        OpenAIReasoningAgent,
        OughtInferenceAgent,
        SquadAgent,
    ]


def get_agent(name: str):
    for agent in get_agents():
        if agent.__name__ == name:
            return agent
    raise ValueError(f"Agent {name} not found")
