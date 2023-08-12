from functools import cache
from typing import Optional

from ice.agents.approval import ApprovalAgent
from ice.agents.augmented import AugmentedAgent
from ice.agents.base import Agent as Agent  # Explicit re-export
from ice.agents.cached import CachedAgent
from ice.agents.fake import FakeAgent
from ice.agents.human import HumanAgent
from ice.agents.openai import OpenAIAgent
from ice.agents.openai import OpenAIChatCompletionAgent
from ice.agents.openai import OpenAIEmbeddingAgent
from ice.agents.openai_reasoning import OpenAIReasoningAgent
from ice.agents.ought_inference import OughtInferenceAgent
from ice.agents.squad import SquadAgent
from ice.mode import Mode

# TODO: Come up with a more reasonable way to make agents optional/pluggable.
try:
    from ice.agents.tfew import TFew
except ImportError:

    class Tfew(Agent):
        def __init__(self, *args, **kwargs):
            ...


MACHINE_AGENTS = {
    "chatgpt": lambda: OpenAIChatCompletionAgent(model="gpt-3.5-turbo"),
    "gpt-4": lambda: OpenAIChatCompletionAgent(model="gpt-4"),
    "embedding-ada": lambda: OpenAIEmbeddingAgent(model="text-embedding-ada-002"),
    "instruct": lambda: OpenAIAgent(),
    "instruct-reasoning": lambda: OpenAIReasoningAgent(),
    "instruct-reasoning-crowd": lambda: OpenAIReasoningAgent(num_workers=8),
    "curie": lambda: OpenAIAgent(model="curie"),
    "qasper": lambda: SquadAgent(),
    "mono-t5": lambda: OughtInferenceAgent(engine="mono-t5-base"),
    "adherence-tfew": lambda: TFew(
        origin_model_name="bigscience/T0_3B",
        lora_weights_path="ice/nn/weights/adherence_tfew_3B.pt",
    ),
    "adherence-tfew-multi": lambda: TFew(
        origin_model_name="bigscience/T0_3B",
        lora_weights_path="ice/nn/weights/adherence_tfew_multi_lite_3B.pt",
    ),
}


@cache
def _get_machine_agent(agent_name: str) -> Agent:
    return MACHINE_AGENTS[agent_name]()


def _get_augmented_agent(agent_name: Optional[str] = None) -> AugmentedAgent:
    h_agent = agent_policy(mode="human", agent_name=agent_name)
    m_agent = agent_policy(mode="machine", agent_name=agent_name)
    return AugmentedAgent(human=h_agent, machine=m_agent)


def _get_approval_agent(agent_name: Optional[str] = None) -> ApprovalAgent:
    h_agent = agent_policy(mode="human", agent_name=agent_name)
    m_agent = agent_policy(mode="machine", agent_name=agent_name)
    return ApprovalAgent(base_agent=m_agent, approval_agent=h_agent)


def agent_policy(mode: Mode, agent_name: Optional[str] = None) -> Agent:
    if mode == "human":
        return HumanAgent()
    elif mode == "augmented":
        return _get_augmented_agent(agent_name)
    elif mode == "augmented-cached":
        return CachedAgent(_get_augmented_agent(agent_name))
    elif mode == "machine":
        return _get_machine_agent(agent_name or "instruct")
    elif mode == "machine-cached":
        return CachedAgent(
            _get_machine_agent(agent_name or "instruct"),
            cache_name=f"{(agent_name or 'instruct').replace('-', '_')}_cached",
        )
    elif mode == "fake" or mode == "test":
        return FakeAgent()
    elif mode == "approval":
        return _get_approval_agent(agent_name)
    else:
        raise ValueError(f"Unknown mode: {mode}")
