from ice.recipe import recipe
from ice.recipes.elicit.outline_utils import parse_outline
from ice.recipes.elicit.qa import elicit_qa
from ice.recipes.elicit.search import elicit_search


def select_keys(d, keys):
    return {k: d[k] for k in keys}


def make_create_outline_prompt(question, papers):
    formatted_cases = [
        "{paper_index}. {title}\n\nAbstract: {unsegmentedAbstract}".format(
            paper_index=index, **paper
        )
        for index, paper in enumerate(papers.values(), 1)
    ]
    formatted_cases_str = "\n\n".join(formatted_cases)
    prompt = f"""# List of papers

{formatted_cases_str}

# Question

The question is: {question}

# Task: Decompose & organize

Task: Decompose the question into a hierarchical outline of topics. Organize the papers based on what topic they are most relevant to.

Outline format example:
- Topic A (papers 1, 4, 8)
  - Subtopic A1 (papers 1, 4)
  - Subtopic A2 (papers 8)
- Topic B (papers 2, 3, 5)
  - Subtopic B1 (papers 2, 3)
  - Subtopic B2 (papers 5)
- Topic C (papers 9)

# Plan

I. Based on the abstracts, write down a comma-separated list of question-relevant topics that each paper distinctly addresses ("I. Question-relevant topics for each paper id:"). Each topic should only be a few words. The topics should serve as good search terms to expand on.
II. Re-organize the papers by question-relevant topics ("II. Paper ids by topic:")
III. Structure the topics in a hierarchical outline in the same format as the outline format example ("III. Hierarchical outline:")
IV. Clean up the outline by removing redundant wording ("IV. Final hierarchical outline:")

# Execution

I. Question-relevant topics for each paper id:"""
    return prompt


def parse_outline(outline_str):
    # A helper function to create a nested outline from a list of lines
    def make_nested_outline(lines, level):
        outline = []
        i = 0
        while i < len(lines):
            line = lines[i]
            # Check the indentation level of the line
            indent = len(line) - len(line.lstrip())
            # If the line is at the current level, add it as a title
            if indent == level:
                title = line.strip("*- ")
                outline.append({"title": title})
                i += 1
            # If the line is indented more than the current level, assume it is a sub-outline
            elif indent > level:
                # Find the end of the sub-outline
                j = i + 1
                while j < len(lines) and len(lines[j]) - len(lines[j].lstrip()) > level:
                    j += 1
                # Recursively parse the sub-outline and add it as a content
                sub_outline = make_nested_outline(lines[i:j], indent)
                outline[-1]["content"] = sub_outline
                i = j
            # If the line is indented less than the current level, ignore it
            else:
                i += 1
        return outline

    # Split the outline string by lines and remove empty ones
    lines = [line for line in outline_str.split("\n") if line.strip()]
    # Parse the outline from the top level
    return make_nested_outline(lines, 0)


async def create_outline(question, papers):
    prompt = make_create_outline_prompt(question, papers)
    completion = await recipe.agent().complete(
        prompt=prompt, stop=None, max_tokens=1024
    )
    answer_split_str = "IV. Final hierarchical outline:"
    if answer_split_str in completion:
        outline_str = completion.split(answer_split_str)[1]
    else:
        followup_prompt = prompt + completion + "\n\nOutline:"
        outline_str = await recipe.agent().complete(
            prompt=followup_prompt, stop=None, max_tokens=512
        )
    outline = parse_outline(outline_str)
    return outline, prompt, completion


async def paper_qa(paper, question):
    return await elicit_qa(question, paper)


def get_excerpts(obj):
    # initialize an empty dictionary
    excerpts = {}
    # loop through the papers in the object
    for paper_id, paper_data in obj["papers"].items():
        for qa_key, qa_results in paper_data["fullTextQaResults"].items():
            # check if the status is success and the value has a most relevant excerpt
            if qa_results["status"] == "success" and qa_results["value"].get(
                "mostRelevantExcerpt"
            ):
                # get the text of the most relevant excerpt
                excerpt_text = qa_results["value"]["mostRelevantExcerpt"]["text"]
                # add the paper id and the excerpt text to the dictionary
                excerpts.setdefault(paper_id, []).append(excerpt_text)
    # return the dictionary
    return excerpts


async def fill_section(question, section_title, papers):
    elicit_response = await elicit_qa(
        root_question=question, qa_question=section_title, papers=papers
    )
    excerpts = get_excerpts(elicit_response)
    return list(excerpts.values())


async def fill_outline(question, outline, papers):
    filled_outline = []
    for section in outline:
        if section.get("content"):
            filled_section = await fill_outline(question, section["content"], papers)
        else:
            filled_section = await fill_section(question, section["title"], papers)
        filled_outline.append({"title": section["title"], "content": filled_section})
    return filled_outline


async def get_papers(question: str, num_papers: int = 10):
    # Retrieve papers from Elicit (without any takeaways or other columns)
    search_response = await elicit_search(question=question, num_papers=num_papers)

    if not "papers" in search_response:
        return "No papers found"

    # Add keys to values
    papers = {k: dict(v, paperId=k) for k, v in search_response["papers"].items()}
    return papers


async def outline(
    question: str = "What is the effect of creatine on cognition?",
):
    # Retrieve papers from Elicit
    papers = await get_papers(question, num_papers=6)

    # Create outline of answer (e.g. pro/con, list of effects; 2-6 points)
    outline, _, _ = await create_outline(question, papers)

    # For each outline point, go through top papers, add relevant quotes
    filled_outline = await fill_outline(question, outline, papers)

    return filled_outline


recipe.main(outline)
