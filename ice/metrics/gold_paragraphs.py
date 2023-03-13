"""
Make a dataframe that contains the paragraphs that contain the gold standard quotes.
"""
import asyncio
from pathlib import Path
from typing import Optional

import pandas as pd
from structlog import get_logger

from ice.cache import diskcache
from ice.evaluation.utils import rouge_compare
from ice.metrics.gold_standards import get_gold_standards
from ice.metrics.gold_standards import list_experiments
from ice.paper import get_paper_paths
from ice.paper import Paper
from ice.paper import Paragraph

log = get_logger()


def get_question_gold_standards(question_short_name: str):
    paper_paths = get_paper_paths()
    question_gold_standards = []
    for paper_path in paper_paths:
        paper = Paper.load(paper_path)
        experiments = list_experiments(
            document_id=paper.document_id, question_short_name=question_short_name
        )
        for experiment in experiments:
            gold_standards = get_gold_standards(
                document_id=paper.document_id,
                question_short_name=question_short_name,
                experiment=experiment,
            )
            if gold_standards:
                assert len(gold_standards) == 1
                gold_standard = gold_standards[0]
                question_gold_standards.append(gold_standard)
    return question_gold_standards


def nonempty_paragraphs(paper):
    for paragraph in paper.paragraphs:
        if paragraph.sentences:
            yield paragraph


def get_recall(quote, paragraph):
    rouge = asyncio.run(rouge_compare([str(paragraph.sentences)], [quote]))
    recall = rouge.rouge_l.r
    return recall


@diskcache()
def get_containing_paragraph(
    document_id: str, quote: str, verbose: bool = False
) -> Optional[Paragraph]:
    """
    Given a document ID and a quote, return the paragraph that the quote is in.
    """
    script_path = Path(__file__).parent
    paper = Paper.load(script_path / ".." / ".." / "papers" / document_id)
    best_recall_paragraph = None
    best_recall = 0.0
    for paragraph in nonempty_paragraphs(paper):
        recall = get_recall(quote, paragraph)
        if recall > best_recall:
            best_recall_paragraph = paragraph
            best_recall = recall
    if best_recall < 0.75 and verbose:
        # Explanations:
        # - Quote is split across two paragraphs
        # - Document paragraphs don't include quote
        log.warning(
            f"""Couldn't find gold standard paragraph for quote

> {quote}

in {document_id}. Best recall was {best_recall:.2f}. Best paragraph was:

> {best_recall_paragraph}"""
        )
    return best_recall_paragraph


def get_gold_paragraph_df(question_short_name: str):
    gold_standards = get_question_gold_standards(question_short_name)

    entries = []
    paragraph_id = 0
    id_to_paragraph = {}

    for gold_standard in gold_standards:
        base_entry = {
            "document_id": gold_standard.document_id,
            "experiment": gold_standard.experiment,
            "answer": gold_standard.answer,
            "classification": gold_standard.classifications[1],
        }
        for quote in gold_standard.quotes:
            entry = base_entry.copy()
            entry["quote"] = quote
            containing_paragraph = get_containing_paragraph(
                entry["document_id"], entry["quote"]
            )
            entry["paragraph"] = str(containing_paragraph)
            entry["paragraph_id"] = paragraph_id
            id_to_paragraph[paragraph_id] = containing_paragraph
            entries.append(entry)
            paragraph_id += 1

    # Convert entries to dataframe
    df = pd.DataFrame(entries)

    # Reorder columns, classification last
    df = df[
        [
            "document_id",
            "experiment",
            "quote",
            "paragraph",
            "paragraph_id",
            "answer",
            "classification",
        ]
    ]

    df = df.rename(
        columns={
            "answer": "paper_gold_answer",
            "classification": "paper_gold_classification",
        }
    )
    return df, id_to_paragraph
