from utils import *
import testDebates

def render_debate_prompt(agent_name: str, debate: Debate, turns_left: int, current_prompt: int) -> str:

    test_debates_instance = testDebates.TestDebates()
    # retrieve correct prompt
    prompts_list = test_debates_instance.get_prompts()

    print("CURRENT NUM: " + str(current_prompt))
    print("CURRENT: " + str(test_debates_instance.get_prompts()))
    promptIn = prompts_list[current_prompt]

    prompt = f"""
    "You are {agent_name}. There are {turns_left} turns left in the debate. {promptIn}
    {render_debate(debate, agent_name)}
    You: "
    """.strip()


    return prompt
# print(render_debate_prompt("Bob", my_debate, 5))
