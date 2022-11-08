from pathlib import Path
from typing import Sequence

from tqdm import tqdm

from ice.metrics.gold_standards import get_gold_standards
from ice.paper import Paper

_paper_dir = Path("/code/papers/")  # fixed in container

def download_paper(document_id: str) -> Paper:
    paper_path = Path(_paper_dir, document_id)
    return Paper.load(paper_path)


def download_papers(
    split: str = "validation", question_short_name: str = "consort_flow"
):
    doc_ids = {
        gs.document_id
        for gs in get_gold_standards(question_short_name=question_short_name)
        if gs.split == split
    }
    paper_files = [f for f in _paper_dir.iterdir() if f.name in doc_ids]
    return [
        Paper.load(f)
        for f in tqdm(paper_files, desc="Loading papers for gold standards")
    ]
