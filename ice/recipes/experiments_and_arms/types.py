from collections.abc import Sequence
from typing import ClassVar
from typing import Generic
from typing import Literal
from typing import NewType
from typing import Protocol
from typing import runtime_checkable
from typing import TypeVar

from pydantic import BaseModel
from pydantic import root_validator
from pydantic import validator
from pydantic.generics import GenericModel

from ice.metrics.gold_standards import ParsedGoldStandardBase
from ice.paper import Paragraph


T = TypeVar("T")

Stage = NewType("Stage", str)


class Sample(BaseModel):
    size: int | Literal["Unclear"] | None = None
    stage: Stage | None = None


class Arm(BaseModel):
    name: str
    description: str
    sample: Sample | None = None

    @root_validator(pre=True)
    def fix_keys(cls, values):
        # Kind of ugly but the yaml in the airtable is in a pretty weird schema
        if isinstance(values, dict) and "arm description" in values:
            values["description"] = values["arm description"]
        if isinstance(values, dict) and "initial sample" in values:
            values["sample"] = values["initial sample"]
        return values


class Experiment(BaseModel):
    name: str
    description: str
    arms: list[Arm]

    @root_validator(pre=True)
    def fix_keys(cls, values):
        # Kind of ugly but the yaml in the airtable is in a pretty weird schema
        if isinstance(values, dict) and "experiment description" in values:
            values["description"] = values["experiment description"]
        return values

    @validator("arms", pre=True)
    def fix_arms(cls, v):
        # Kind of ugly but the yaml in the airtable is in a pretty weird schema
        if isinstance(v, dict):
            return [Arm.parse_obj(vals | dict(name=k)) for k, vals in v.items()]
        return v


class ExperimentsArms(ParsedGoldStandardBase):
    question_short_name: ClassVar[str] = "experiments_arms"
    experiments: list[Experiment]

    @validator("experiments", pre=True)
    def validate_experiments(cls, v):
        # Kind of ugly but the yaml in the airtable is in a pretty weird schema
        if isinstance(v, dict):
            return [Experiment.parse_obj(vals | dict(name=k)) for k, vals in v.items()]
        return v


ReasoningStage = Literal["reasoning", "helpfulness", "answer"]


class PassageWithReasoning(GenericModel, Generic[T]):
    passage: Sequence[str]
    reasoning: str
    helpfulness: str | None = None
    score: float | None = None
    final_answer: T | None = None


@runtime_checkable
class MultipartReasoningPrompt(Protocol):
    def __call__(
        self,
        paragraphs: Sequence[str],
        helpfulness: str | None = None,
        reasoning: str | None = None,
    ) -> str:
        pass
