import asyncio

import streamlit as st

from ice.recipes.elicit.outline import create_outline
from ice.recipes.elicit.outline import fill_outline
from ice.recipes.elicit.outline import get_papers


def show_outline(outline, level=1):
    st.write(f"#{'#' * level} {outline}")
    try:
        for section in outline["content"]:
            show_outline(section, level=level + 1)
    except:
        pass


def main():
    question = st.text_input("Question")
    status = st.empty()
    results = st.empty()
    if not question:
        return

    status.markdown("Retrieving papers from Elicit...")
    papers = asyncio.run(get_papers(question, num_papers=6))
    status.markdown(
        "Retrieved {} papers. Creating answer outline...".format(len(papers))
    )

    for i, (paper_key, paper_value) in enumerate(papers.items(), 1):
        st.write(f"{i} - {paper_value['title']}")

    outline, prompt, completion = asyncio.run(create_outline(question, papers))

    with st.expander("Prompt"):
        st.code(prompt)

    with st.expander("Completion"):
        st.code(completion)

    status.markdown("Created outline. Filling in outline...")
    filled_outline = asyncio.run(fill_outline(question, outline, papers))

    with results:
        for section in filled_outline:
            show_outline(section)
    status.markdown(" ")


if __name__ == "__main__":
    main()
