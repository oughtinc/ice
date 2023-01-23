from collections.abc import Sequence
from typing import ClassVar
from typing import Literal
from typing import Optional
from typing import Type
from typing import Union

from pydantic import BaseModel
from pydantic import root_validator
from pydantic import validator

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


def _not_yet_collected_is_none(value: object) -> Optional[object]:
    if value == NOT_YET_COLLECTED:
        return None
    return value


def _maybe_dict_to_sequence(
    constructor: Type[BaseModel], maybe_dict: object
) -> Union[object, Sequence[BaseModel]]:
    if isinstance(maybe_dict, dict):
        return [
            constructor.parse_obj(vals | dict(name=k)) for k, vals in maybe_dict.items()
        ]
    return maybe_dict


class SampleSize(BaseModel):
    description: Optional[str] = None
    reasoning: Optional[str] = None
    n: Union[int, Literal["Not mentioned"]]
    quotes: Sequence[str]


class Reason(BaseModel):
    name: str
    description: Optional[str] = None
    reasoning: Optional[str] = None
    n: Union[int, Literal["Not mentioned"]]


class SampleSizeWithReasons(SampleSize):
    reasons: Optional[Union[Literal["Not mentioned"], Sequence[Reason]]] = None

    @validator("reasons", pre=True)
    def validate_reasons(cls, v):
        return _maybe_dict_to_sequence(Reason, v)


class Received(BaseModel):
    description: Optional[str] = None
    quotes: Sequence[str]


class Analysis(SampleSize):
    name: str


class Arm(BaseModel):
    name: str
    allocated: Union[Optional[Literal["Not mentioned"]], SampleSize]
    received: Union[Optional[Literal["Not mentioned"]], Received]
    attrition: Optional[SampleSizeWithReasons]
    analyzed: Optional[Sequence[Analysis]]

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
    assessed: Union[Literal["Not mentioned"], SampleSize]
    excluded: Union[Literal["Not mentioned"], SampleSizeWithReasons]
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
    description: Optional[str] = None
    reasoning: Optional[str] = None
    enrolment: Optional[Enrolment]
    arms: Optional[Sequence[Arm]]

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
    question_short_name: ClassVar[str] = "consort_flow_v2"
    experiments: list[Experiment]

    @validator("experiments", pre=True)
    def validate_experiments(cls, v):
        return _maybe_dict_to_sequence(Experiment, v)
