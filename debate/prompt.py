from ice.recipes.primer.debate.utils import *


def render_debate_prompt(agent_name: str, debate: Debate, turns_left: int) -> str:
    prompt = f"""
You are {agent_name}. There are {turns_left} turns left in the debate. You are trying to win the debate using reason and evidence. Do not repeat yourself. Use 1-2 sentences per turn.

{render_debate(debate, agent_name)}
You: "
""".strip()
    return prompt


#print(render_debate_prompt("Bob", my_debate, 5))

# You are {agent_name}. There are {turns_left} turns left in the debate. You are trying to win the debate using reason and evidence. No more than 1-2 sentences per turn.

'''
from ice.recipes.primer.debate.utils import *


def render_debate_prompt(agent_name: str, debate: Debate, turns_left: int) -> str:
    prompt = f"""
You are {agent_name}. There are {turns_left} turns left in the debate. You are trying to win the debate using reason and evidence. No more than 1-2 sentences per turn.

{render_debate(debate, agent_name)}
You: "
""".strip()
    return prompt
'''
