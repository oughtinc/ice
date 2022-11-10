from typing import ClassVar, Literal, Sequence, Type
from pydantic import BaseModel, root_validator, validator

from ice.metrics.gold_standards import ParsedGoldStandardBase

NOT_YET_COLLECTED = "Gold standard not yet collected"


def _fix_keys(model_values: object, correct_key_mapping: dict[str, str]) -> object:
    if isinstance(model_values, dict):
        new_dict = dict()
        for key, value in model_values.items():
            if key in correct_key_mapping:
                new_dict[correct_key_mapping[key]] = value
            else:
                new_dict[key] = value
        return new_dict
    return model_values


def _not_yet_collected_is_none(value: object) -> object | None:
    if value == NOT_YET_COLLECTED:
        return None
    return value


def _maybe_dict_to_sequence(
    constructor: Type[BaseModel], maybe_dict: object
) -> object | Sequence[BaseModel]:
    if isinstance(maybe_dict, dict):
        return [
            constructor.parse_obj(vals | dict(name=k)) for k, vals in maybe_dict.items()
        ]
    return maybe_dict


class SampleSize(BaseModel):
    description: str | None = None
    reasoning: str | None = None
    n: int | Literal["Not mentioned"]
    quotes: Sequence[str]


class Reason(BaseModel):
    name: str
    description: str | None = None
    reasoning: str | None = None
    n: int | Literal["Not mentioned"]


class SampleSizeWithReasons(SampleSize):
    reasons: Literal["Not mentioned"] | Sequence[Reason]

    @validator("reasons", pre=True)
    def validate_reasons(cls, v):
        return _maybe_dict_to_sequence(Reason, v)


class Received(BaseModel):
    description: str | None = None
    quotes: Sequence[str]


class Analysis(SampleSize):
    name: str


class Arm(BaseModel):
    name: str
    allocated: None | Literal["Not mentioned"] | SampleSize
    received: None | Literal["Not mentioned"] | Received
    attrition: None | SampleSizeWithReasons
    analyzed: None | Sequence[Analysis]

    @validator("analyzed", pre=True)
    def validate_analyzed(cls, v):
        return _maybe_dict_to_sequence(Analysis, v)

    @root_validator(pre=True)
    def not_yet_collected_always_none(cls, values):
        if isinstance(values, dict):
            for key, value in values.items():
                if value == NOT_YET_COLLECTED:
                    values[key] = None
        return _fix_keys(
            values,
            {
                "Allocated to arm": "allocated",
                "Received allocated intervention": "received",
                "-> Attrition": "attrition",
                "Analysed": "analyzed",
            },
        )


class Enrolment(BaseModel):
    assessed: Literal["Not mentioned"] | SampleSize
    excluded: Literal["Not mentioned"] | SampleSizeWithReasons
    randomized: SampleSize

    @root_validator(pre=True)
    def fix_keys(cls, values):
        return _fix_keys(
            values,
            {
                "Assessed for eligibility": "assessed",
                "-> Excluded": "excluded",
                "Randomised": "randomized",
            },
        )


class Experiment(BaseModel):
    name: str
    description: str | None = None
    reasoning: str | None = None
    enrolment: Enrolment | None
    arms: Sequence[Arm] | None

    _enrolment_to_none = validator("enrolment", pre=True, allow_reuse=True)(
        _not_yet_collected_is_none
    )

    @validator("arms", pre=True)
    def validate_arms(cls, v):
        return _maybe_dict_to_sequence(Arm, v)

    @root_validator(pre=True)
    def fix_keys(cls, values):
        return _fix_keys(
            values, {"Enrolment": "enrolment", "assigning to arms and after": "arms"}
        )


class ConsortFlow(ParsedGoldStandardBase):
    question_short_name: ClassVar[str] = "consort_flow"
    experiments: list[Experiment]

    @validator("experiments", pre=True)
    def validate_experiments(cls, v):
        return _maybe_dict_to_sequence(Experiment, v)
