from ice.agents.base import Agent
from ice.recipe import recipe
from ice.recipes.primer.debate.prompt import *

async def debate(question: str = "Should we ban guns?", number_of_turns: int = 8, agent_names: tuple[Name, Name] = ("Alice", "Bob")):
    agents = [recipe.agent(), recipe.agent()]
    debate_history = initialize_debate(question, agent_names)
    turns_left = number_of_turns
    while turns_left > 0:
        for agent, name in zip(agents, agent_names):
            prompt = render_debate_prompt(name, debate_history, turns_left)
            answer = await agent.answer(prompt=prompt, multiline=False)
            debate_history.append((name, answer.strip('" ')))
            turns_left -= 1
    return render_debate(debate_history)

recipe.main(debate)