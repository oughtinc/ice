from collections.abc import Iterator
from collections.abc import Sequence
from functools import cache
from functools import cached_property
from pathlib import Path
from typing import Any
from typing import ClassVar
from typing import Generic
from typing import Literal
from typing import Optional
from typing import overload
from typing import Type
from typing import TypeVar

import pandas as pd
from pydantic import BaseModel
from pydantic.generics import GenericModel
from structlog.stdlib import get_logger

from ice.paper import Paper
from ice.settings import settings

log = get_logger()


class ParsedGoldStandardBase(BaseModel):
    question_short_name: ClassVar[str]


ParsedGoldStandardType = TypeVar("ParsedGoldStandardType", bound=ParsedGoldStandardBase)

GoldStandardSplit = Literal["test", "validation", "iterate"]


class GoldStandard(GenericModel, Generic[ParsedGoldStandardType]):
    document_id: str
    question_short_name: str
    experiment: str
    answer: str
    classifications: Sequence[Optional[str]] = []
    quotes: list[str]
    split: Optional[str] = None
    answer_model: Optional[Type[ParsedGoldStandardType]] = None

    @cached_property
    def parsed_answer(self) -> Optional[ParsedGoldStandardType]:
        return (
            _parse_answer(self.answer, self.answer_model)
            if self.answer_model is not None
            else None
        )

    class Config:
        keep_untouched = (cached_property,)
        fields = dict(answer_model=dict(exclude=True))


def _parse_answer(
    _answer: str, model: Type[ParsedGoldStandardType]
) -> ParsedGoldStandardType:
    from yaml import CLoader as Loader
    from yaml import load

    data = load(_answer, Loader=Loader)
    return model.parse_obj(data)


@cache
def retrieve_gold_standards_df() -> pd.DataFrame:
    df = pd.read_csv(settings.GOLD_STANDARDS_CSV_PATH)
    df = add_quotes_column(df)
    df = add_classifications_column(df)
    return df


def value_in_column(column: str, value: str, df: pd.DataFrame) -> bool:
    return df[column].str.contains(value, regex=False).any()


def add_quotes_column(df: pd.DataFrame) -> pd.DataFrame:
    quotes = df[[col for col in df.columns if col.startswith("quote_")]]
    df["quotes"] = quotes.apply(
        lambda row: [row[col] for col in quotes.columns if not pd.isna(row[col])],
        axis=1,
    )
    return df


def add_classifications_column(df: pd.DataFrame) -> pd.DataFrame:
    classifications = df[
        [col for col in df.columns if col.startswith("classification_")]
    ]

    ordered_classification_cols = classifications.columns.sort_values()

    df["classifications"] = classifications.apply(
        lambda row: [
            None if pd.isna(row[col]) else row[col]
            for col in ordered_classification_cols
        ],
        axis=1,
    )
    return df


def _standards_df_to_gold_standards(
    df: pd.DataFrame, answer_model: Optional[Type[ParsedGoldStandardType]]
) -> list[GoldStandard[ParsedGoldStandardType]]:
    return [
        GoldStandard.parse_obj(record | dict(answer_model=answer_model))
        for record in df.to_dict("records")
    ]


def list_experiments(
    *, document_id: Optional[str] = None, question_short_name: Optional[str] = None
) -> list[str]:
    df = retrieve_gold_standards_df()
    df = select_column_values(
        df, dict(document_id=document_id, question_short_name=question_short_name)
    )
    experiments = df.experiment.dropna().unique().tolist()
    return [experiment for experiment in experiments if experiment != "All"]


def select_column_values(
    df: pd.DataFrame, column_values: dict[str, Optional[str]]
) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)
    for column, value in column_values.items():
        if value is not None:
            if not value_in_column(column, value, df):
                log.warning(
                    "Removing all records because filter does not match",
                    column=column,
                    value=value,
                )
            mask &= df[column] == value
    return df.loc[mask]


_paper_dir = settings.PAPER_DIR


def load_paper(document_id: str) -> Paper:
    return Paper.load(Path(_paper_dir, document_id))


def load_papers(split: str, question_short_name: str):
    doc_ids = {
        gs.document_id
        for gs in get_gold_standards(question_short_name=question_short_name)
        if gs.split == split
    }
    return [load_paper(doc_id) for doc_id in doc_ids]


def generate_papers_and_golds(
    split: str,
    gold_standard_type: Type[ParsedGoldStandardType],
) -> Iterator[tuple[Paper, GoldStandard[ParsedGoldStandardType]]]:
    papers = load_papers(split, gold_standard_type.question_short_name)

    for paper in papers:
        gold = get_gold_standard(
            document_id=paper.document_id,
            question_short_name=gold_standard_type.question_short_name,
            model_type=gold_standard_type,
        )
        if not gold:
            log.warning(
                "Did not find gold standard",
                document_id=paper.document_id,
                question_short_name=gold_standard_type.question_short_name,
            )
            continue
        yield paper, gold


@overload
def get_gold_standards(
    *,
    document_id: Optional[str] = None,
    question_short_name: Optional[str] = None,
    experiment: Optional[str] = None,
    model_type: None = None,
) -> list[GoldStandard[Any]]:
    ...


@overload
def get_gold_standards(
    *,
    model_type: Type[ParsedGoldStandardType],
    document_id: Optional[str] = None,
    question_short_name: Optional[str] = None,
    experiment: Optional[str] = None,
) -> list[GoldStandard[ParsedGoldStandardType]]:
    ...


def get_gold_standards(
    *,
    document_id: Optional[str] = None,
    question_short_name: Optional[str] = None,
    experiment: Optional[str] = None,
    model_type: Optional[Type[ParsedGoldStandardType]] = None,
) -> list[GoldStandard[ParsedGoldStandardType]]:
    df = retrieve_gold_standards_df()

    filters = dict(
        document_id=document_id,
        question_short_name=question_short_name,
        experiment=experiment,
    )

    df = select_column_values(df, filters)

    return _standards_df_to_gold_standards(df, model_type)


@overload
def get_gold_standard(
    *,
    document_id: Optional[str] = None,
    question_short_name: Optional[str] = None,
    experiment: Optional[str] = None,
    model_type: None = None,
) -> Optional[GoldStandard[Any]]:
    ...


@overload
def get_gold_standard(
    *,
    model_type: Type[ParsedGoldStandardType],
    document_id: Optional[str] = None,
    question_short_name: Optional[str] = None,
    experiment: Optional[str] = None,
) -> Optional[GoldStandard[ParsedGoldStandardType]]:
    ...


def get_gold_standard(
    *,
    document_id: Optional[str] = None,
    question_short_name: Optional[str] = None,
    experiment: Optional[str] = None,
    model_type: Optional[Type[ParsedGoldStandardType]] = None,
) -> Optional[GoldStandard[ParsedGoldStandardType]]:
    gold_standards = get_gold_standards(
        document_id=document_id,
        question_short_name=question_short_name,
        experiment=experiment,
        model_type=model_type,
    )

    if len(gold_standards) == 0:
        return None

    if len(gold_standards) > 1:
        raise ValueError(
            f"Found more than one gold standard for experiment={experiment}, question_short_name={question_short_name}, document_id={document_id}"
        )

    return gold_standards[0]
