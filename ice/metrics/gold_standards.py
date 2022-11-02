from collections.abc import Sequence
from functools import cache
from functools import cached_property
from typing import Any, Literal
from typing import Generic
from typing import overload
from typing import Type
from typing import TypeVar

import pandas as pd

from pydantic import BaseModel
from pydantic.generics import GenericModel
from structlog.stdlib import get_logger
from yaml import CLoader as Loader
from yaml import load

from ice.settings import settings

log = get_logger()

ModelType = TypeVar("ModelType", bound=BaseModel)

GoldStandardSplit = Literal["test", "validation", "iterate"]

# TODO: merge with RecipeResult
class GoldStandard(GenericModel, Generic[ModelType]):
    document_id: str
    question_short_name: str
    experiment: str
    answer: str
    classifications: Sequence[str | None] = []
    quotes: list[str]
    split: str | None = None
    answer_model: Type[ModelType] | None = None

    @cached_property
    def parsed_answer(self) -> ModelType | None:
        return (
            _parse_answer(self.answer, self.answer_model)
            if self.answer_model is not None
            else None
        )

    class Config:
        keep_untouched = (cached_property,)
        fields = dict(answer_model=dict(exclude=True))


def _parse_answer(_answer: str, model: Type[ModelType]) -> ModelType:
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
    df: pd.DataFrame, answer_model: Type[ModelType] | None
) -> list[GoldStandard[ModelType]]:
    return [
        GoldStandard.parse_obj(record | dict(answer_model=answer_model))
        for record in df.to_dict("records")
    ]


def list_experiments(
    *, document_id: str | None = None, question_short_name: str | None = None
) -> list[str]:
    df = retrieve_gold_standards_df()
    df = select_column_values(
        df, dict(document_id=document_id, question_short_name=question_short_name)
    )
    experiments = df.experiment.dropna().unique().tolist()
    return [experiment for experiment in experiments if experiment != "All"]


def select_column_values(
    df: pd.DataFrame, column_values: dict[str, str | None]
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


@overload
def get_gold_standards(
    *,
    document_id: str | None = None,
    question_short_name: str | None = None,
    experiment: str | None = None,
    model_type: None = None,
) -> list[GoldStandard[Any]]:
    ...


@overload
def get_gold_standards(
    *,
    model_type: Type[ModelType],
    document_id: str | None = None,
    question_short_name: str | None = None,
    experiment: str | None = None,
) -> list[GoldStandard[ModelType]]:
    ...


def get_gold_standards(
    *,
    document_id: str | None = None,
    question_short_name: str | None = None,
    experiment: str | None = None,
    model_type: Type[ModelType] | None = None,
) -> list[GoldStandard[ModelType]]:
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
    document_id: str | None = None,
    question_short_name: str | None = None,
    experiment: str | None = None,
    model_type: None = None,
) -> GoldStandard[Any] | None:
    ...


@overload
def get_gold_standard(
    *,
    model_type: Type[ModelType],
    document_id: str | None = None,
    question_short_name: str | None = None,
    experiment: str | None = None,
) -> GoldStandard[ModelType] | None:
    ...


def get_gold_standard(
    *,
    document_id: str | None = None,
    question_short_name: str | None = None,
    experiment: str | None = None,
    model_type: Type[ModelType] | None = None,
) -> GoldStandard[ModelType] | None:
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
