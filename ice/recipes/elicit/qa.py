from typing import Optional
from urllib.parse import urljoin

from structlog.stdlib import get_logger

from ice.recipe import recipe
from ice.recipes.elicit.common import send_elicit_request
from ice.recipes.elicit.search import get_elicit_backend

log = get_logger()

ELICIT_QA_ENDPOINT = "full-text-qa"


def get_span_container(paper, source):
    return paper[source] if source == "abstract" else paper["body"]["value"]


def get_span_paragraph(container, paragraph_index):
    return container["paragraphs"][paragraph_index]


def get_span_text(paragraph, sentence_start, sentence_stop):
    sentences = paragraph["sentences"][sentence_start:sentence_stop]
    return " ".join(sentences)


def augment_qa_response(response, papers):
    for paper_id, paper_data in response["papers"].items():
        for qa_key, qa_data in paper_data["fullTextQaResults"].items():
            # Skip if the query failed or no excerpt was found
            if qa_data["status"] != "success" or not qa_data["value"].get(
                "mostRelevantExcerpt"
            ):
                continue
            # Get the span and its source, paragraph index, and sentence range
            span = qa_data["value"]["mostRelevantExcerpt"]["spans"][0]
            source, paragraph_index, sentence_start, sentence_stop = (
                span["source"],
                span["paragraphIndex"],
                span["sentenceStart"],
                span["sentenceStop"],
            )
            # Get the text of the span from the paper
            container = get_span_container(papers[paper_id], source)
            paragraph = get_span_paragraph(container, paragraph_index)
            span_text = get_span_text(paragraph, sentence_start, sentence_stop)
            # Add the span text to the response
            qa_data["value"]["mostRelevantExcerpt"]["text"] = span_text
    return response


async def elicit_qa(
    root_question: str = "What is the effect of creatine on cognition?",
    qa_question: str = "What was the population?",
    papers: Optional[dict] = None,
):
    cells = [
        dict(paper, column={"type": "custom_question", "value": qa_question})
        for paper in (papers or dict()).values()
    ]
    request_body = {"rootQuestion": root_question, "cells": cells}
    backend = await get_elicit_backend()
    endpoint = urljoin(backend, ELICIT_QA_ENDPOINT)
    response = send_elicit_request(request_body=request_body, endpoint=endpoint)
    # Augment the response with the text of the extract spans
    response = augment_qa_response(response, papers)
    return response


async def elicit_qa_cli(
    root_question: str = "What is the effect of creatine on cognition?",
    qa_question: str = "What was the population?",
):
    response = await elicit_qa(root_question, qa_question)
    return response


recipe.main(elicit_qa_cli)

# Example result:
# {
#     'papers': {
#         'deb4f9cf49a8f1d43e6db4c0cfe543c982911ded': {
#             'fullTextQaResults': {
#                 'custom_question-What was the key result?': {
#                     'status': 'success',
#                     'value': {
#                         'rephrasedQuestion': None,
#                         'mostRelevantExcerpt': {
#                             'spans': [
#                                 {
#                                     'source': 'abstract',
#                                     'paragraphIndex': 0,
#                                     'sentenceStart': 0,
#                                     'sentenceStop': None
#                                 }
#                             ],
#                             'text': 'Background and aims: Creatine is a supplement used by sportsmen to increase athletic performance by improving energy supply to muscle tissues. It is also an essential brain compound and some hypothesize that it aids cognition by improving energy supply and neuroprotection. The aim of this systematic review is to investigate the effects of oral creatine administration on cognitive function in healthy individuals. Methods: A search of multiple electronic databases was performed for the identification of randomized clinical trials (RCTs) examining the cognitive effects of oral creatine supplementation in healthy individuals. Results: Six studies (281 individuals) met our inclusion criteria. Generally, there was evidence that short term memory and intelligence/reasoning may be improved by creatine administration. Regarding other cognitive domains, such as long‐term memory, spatial memory, memory scanning, attention, executive function, response inhibition, word fluency, reaction time and mental fatigue, the results were conflicting. Performance on cognitive tasks stayed unchanged in young individuals. Vegetarians responded better than meat‐eaters in memory tasks but for other cognitive domains no differences were observed. Conclusions: Oral creatine administration may improve short‐term memory and intelligence/reasoning of healthy individuals but its effect on other cognitive domains remains unclear. Findings suggest potential benefit for aging and stressed individuals. Since creatine is safe, future studies should include larger sample sizes. It is imperative that creatine should be tested on patients with dementias or cognitive impairment. HIGHLIGHTSOral creatine supplementation improves memory of healthy adults.Findings suggest potential benefit for aging and stressed individuals.Future trials should investigate the effect of creatine administration on individuals with dementia or mild cognitive impairment.'
#                         },
#                         'answer': 'Oral creatine supplementation improves memory of healthy adults',
#                         'mostRelevantSpan': None,
#                         'subResults': None
#                     }
#                 }
#             }
#         }
#     }
# }
