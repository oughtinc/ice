Question = str
Answer = str
Subs = list[tuple[Question, Answer]]


def render_background(subs: Subs) -> str:
    if not subs:
        return ""
    subs_text = "\n\n".join(f"Q: {q}\nA: {a}" for (q, a) in subs)
    return f"Here is relevant background information:\n\n{subs_text}\n\n"


def make_qa_prompt(question: str, subs: Subs) -> str:
    background_text = render_background(subs)
    return f"""{background_text}Answer the following question, using the background information above where helpful:

Question: "{question}"
Answer: "
""".strip()
