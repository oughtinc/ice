from utils import *
from testDebates import test_debates_instance

def render_debate_prompt(agent_name: str, debate: Debate, turns_left: int) -> str:

    # retrieve correct prompt
    prompts_list = test_debates_instance.get_prompts()
    print("CURRENT: " + str(test_debates_instance.get_current_prompt()))
    promptIn = prompts_list[test_debates_instance.get_current_prompt()]

    prompt = f"""
    "You are {agent_name}. There are {turns_left} turns left in the debate. {promptIn}
    {render_debate(debate, agent_name)}
    You: "
    """.strip()


    return prompt
print(render_debate_prompt("Bob", my_debate, 5))
