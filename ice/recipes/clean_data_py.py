import csv
import re
from transformers import AutoTokenizer
import random
import json
tokenizer = transformers.GPT2Tokenizer.from_pretrained("gpt2")

def truncate(string, max_tokens):
    return tokenizer.decode(tokenizer.encode(string)[:max_tokens])

with open("ft_data.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    data = [row for row in reader]

data = [d for d in data if d["cited_papers"] == "True"]
print("Number of samples:", len(data))
random.seed(31415)
random.shuffle(data)

PROMPT = """This is an article about how to write an ideal academic summary.

Overall question: {question}
Let's write a summary step by step.

Below are 4 relevant papers.

{paper_str}

Let's summarize each paper individually first.

Summaries (starting with paper 1):"""

COMPLETION = """
{reasoning_str}

Using the 4 summaries above, let's write an overall ideal summary for the question.
Let's think step by step.

Ideal overall summary: {summary}"""

PAPERS = """Paper {i}: {title}
Reference: {reference}
Abstract: {abstract}"""

REASONING = """Summary for paper {i}: {title}
Let's think step by step about this paper helps us answer the question: {question}

Question relevant summary for paper {i}: {summary}"""

ABSTRACT_MAX_TOKENS = 300

def mean(l):
    return sum(l)/len(l) if len(l) > 0 else 0

def best_string_match(string1, string2):
    return mean([int(s1 == s2) for s1, s2 in zip(string1.split(), string2.split())])


def process_sample(sample, abstract_max_tokens=ABSTRACT_MAX_TOKENS, end_token=tokenizer.eos_token):
    prompt = sample["prompt"]

    titles = re.findall(r"Paper: (.+)\n", prompt)
    fuzzy_citations = re.findall(r"Reference: (.+)\n", prompt)
    fuzzy_citations = [c.split(" (")[0] for c in fuzzy_citations]
    fuzzy_citations_to_titles = {c: t for c, t in zip(fuzzy_citations, titles)}

    abstracts = [sample[f"abstract_{i}"] for i in range(1, 5)]
    citations = [sample[f"citation_{i}"] for i in range(1, 5)]
    # Use best string match to find the best title for each citation
    titles = []
    for citation in zip(citations):
        citation = "".join(citation).split(",")[0]
        best_fuzzy_citation = max(fuzzy_citations, key=lambda t: best_string_match(citation, t))
        titles.append(fuzzy_citations_to_titles[best_fuzzy_citation])


    summaries = [sample[f"paper_{i}_answer"] for i in range(1, 5)]

    question = sample["question"]

    paper_str = "\n\n".join(
        [
            PAPERS.format(
                i=i + 1,
                title=title,
                reference=citation,
                abstract=truncate(abstract, abstract_max_tokens),
            )
            for i, (title, citation, abstract) in enumerate(
                zip(titles, citations, abstracts)
            )
        ]
    )

    assert len(summaries) == len(titles), f"N Summaries {len(summaries)} != N Titles {len(titles)}"
    reasoning_str = "\n\n".join(
        [
            REASONING.format(
                i=i + 1,
                title=title,
                question=question,
                summary=summary,
            )
            for i, (title, summary) in enumerate(zip(titles, summaries))
        ]
    )

    prompt = PROMPT.format(
        question=question,
        paper_str=paper_str,
    )

    print(sample["summary"])
    completion = COMPLETION.format(
        reasoning_str=reasoning_str,
        summary=sample["summary"],
    )

    return prompt, completion

def create_sample(sample, max_total_tokens=2030):
    max_abstract_tokens = ABSTRACT_MAX_TOKENS
    prompt, completion = process_sample(sample, max_abstract_tokens)
    total_tokens = len(tokenizer.encode(prompt+completion))
    while total_tokens > max_total_tokens and max_abstract_tokens > 0:
        max_abstract_tokens -= 10
        print("Reducing tokens in abstract...", max_abstract_tokens)
        prompt, completion = process_sample(sample, max_abstract_tokens)
        total_tokens = len(tokenizer.encode(prompt+completion))
    return prompt, " "+completion+"<|endoftext|>"

data = [create_sample(sample) for sample in data]

# 40 samples for validation and 40 samples for testing

train_data = data[:150]
val_data = data[150:]
#test_data = data

def dump_data(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        for prompt, completion in data:
            f.write(json.dumps({"prompt": prompt, "completion": completion})+"\n")


for i in range(10):
    print(val_data[i][0])
    print("======")
    print(val_data[i][1])

#dump_data(train_data, "trainT5V2.jsonl")
#dump_data(val_data, "valT5V2.jsonl")
#dump_data(test_data, "testV2.jsonl")