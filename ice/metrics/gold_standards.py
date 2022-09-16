from collections.abc import Sequence
from functools import cache

import pandas as pd

from pydantic import BaseModel
from structlog.stdlib import get_logger

from ice.settings import settings

log = get_logger()


# TODO: merge with RecipeResult
class GoldStandard(BaseModel):
    document_id: str
    question_short_name: str
    experiment: str
    answer: str
    classifications: Sequence[str | None] = []
    quotes: list[str]
    split: str | None = None


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


def standards_df_to_gold_standards(df: pd.DataFrame) -> list[GoldStandard]:
    return [GoldStandard.parse_obj(record) for record in df.to_dict("records")]


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


def get_gold_standards(
    *,
    document_id: str | None = None,
    question_short_name: str | None = None,
    experiment: str | None = None,
) -> list[GoldStandard]:
    df = retrieve_gold_standards_df()

    filters = dict(
        document_id=document_id,
        question_short_name=question_short_name,
        experiment=experiment,
    )

    df = select_column_values(df, filters)

    return standards_df_to_gold_standards(df)


def get_gold_standard(
    *,
    document_id: str | None = None,
    question_short_name: str | None = None,
    experiment: str | None = None,
) -> GoldStandard | None:
    gold_standards = get_gold_standards(
        document_id=document_id,
        question_short_name=question_short_name,
        experiment=experiment,
    )

    if len(gold_standards) == 0:
        return None

    if len(gold_standards) > 1:
        raise ValueError(
            f"Found more than one gold standard for experiment={experiment}, question_short_name={question_short_name}, document_id={document_id}"
        )

    return gold_standards[0]
