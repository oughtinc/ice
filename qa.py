from ice.recipe import recipe

DEFAULT_CONTEXT = "We're running a hackathon on 9/9/2022 to decompose complex reasoning tasks into subtasks that are easier to automate & evaluate with language models. Our team is currently breaking down reasoning about the quality of evidence in randomized controlled trials into smaller tasks e.g. placebo, intervention adherence rate, blinding procedure, etc."

DEFAULT_QUESTION = "What is happening on 9/9/2022?"

def levenshteinDistance(s1, s2):
    """Get the Levenshtein distance between two strings."""
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]

def make_qa_prompt(context: str, question: str) -> str:
    return f"""
Background text: "{context}"

Answer the following question about the background text above:

Question: "{question}"
Answer: Let's think step by step.
""".strip()

def make_updated_prompt(prev_response: str, original_question: str) -> str:
    return f"""
    {prev_response}

    Now attempt to improve the most recent answer to the initial question (which was: "{original_question}").

    Answer: 
    """.strip()


async def answer(
    context: str = DEFAULT_CONTEXT, question: str = DEFAULT_QUESTION, iters: int = 5
) -> str:
    prompt = make_qa_prompt(context, question)
    answer = (await recipe.agent().answer(prompt=prompt)).strip('" ')

    for i in range(iters):
        prompt_plus_answer = prompt + ' ' + answer
        prompt = make_updated_prompt(prompt_plus_answer, question)
        prev_answer = answer
        answer = (await recipe.agent().answer(prompt=prompt)).strip('" ')
        answer_dist = levenshteinDistance(prev_answer, answer)
        print(f"Refinement {i + 1}; Levenshtein distance: {answer_dist}")
        if answer_dist < 3:
            break

    return answer

recipe.main(answer)