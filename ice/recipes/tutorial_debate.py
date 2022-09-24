from ice.agents.base import Agent
from ice.recipe import Recipe


Name = str
Message = str
Turn = tuple[Name, Message]
Debate = list[Turn]


def initialize_debate(question: Message) -> Debate:
    return [
        ("Question", question),
        ("Alice", "I'm in favor."),
        ("Bob", "I'm against."),
    ]


def render_debate(debate: Debate, self_name: Name | None = None) -> str:
    debate_text = ""
    for speaker, text in debate:
        if speaker == self_name:
            speaker = "You"
        debate_text += f'{speaker}: "{text}"\n'
    return debate_text.strip()


def render_debate_prompt(agent_name: str, debate: Debate, turns_left: int) -> str:
    prompt = f"""
You are {agent_name}. There are {turns_left} turns left in the debate. You are trying to win the debate using reason and evidence. Don't repeat yourself. No more than 1-2 sentences per turn.

{render_debate(debate, agent_name)}
You: "
""".strip()
    return prompt


class DebateRecipe(Recipe):
    async def run(self, question: str = "Should we legalize all drugs?"):
        agents = [self.agent(), self.agent()]
        agent_names = ["Alice", "Bob"]
        debate = initialize_debate(question)
        turns_left = 8
        while turns_left > 0:
            for agent, agent_name in zip(agents, agent_names):
                turn = await self.turn(debate, agent, agent_name, turns_left)
                debate.append(turn)
                turns_left -= 1
        return render_debate(debate)

    async def turn(
        self, debate: Debate, agent: Agent, agent_name: Name, turns_left: int
    ):
        prompt = render_debate_prompt(agent_name, debate, turns_left)
        answer = await agent.answer(prompt=prompt, multiline=False, max_tokens=100)
        return (agent_name, answer.strip('" '))
