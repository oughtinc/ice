import typing as t
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic.generics import GenericModel

from ice.paper import Paper


def _to_str(paper: Paper, start: int, end: int) -> str:
    return " ".join(list(paper.sentences())[start:end])


class Selection(BaseModel):
    p: Paper
    start: int
    end: int
    is_gs: Optional[bool] = None

    # TODO: validate on creation

    def context(self, pre: int, post: int):
        idxs_before = range(max(0, self.start - pre), self.start)
        idxs_after = range(
            self.end, min(len(list(self.p.sentences())), self.end + post)
        )
        before = [
            Selection(p=self.p, start=start, end=start + 1) for start in idxs_before
        ]
        after = [Selection(p=self.p, start=end - 1, end=end) for end in idxs_after]
        return before, after

    @t.final
    @property
    def original(self):
        return _to_str(self.p, self.start, self.end)

    def __str__(self):
        return _to_str(self.p, self.start, self.end)

    class Config:
        copy_on_model_validation = False


def make_selector(paper: Paper) -> t.Callable[[int, int], Selection]:
    def s(start: int, end: int) -> Selection:
        return Selection.construct(p=paper, start=start, end=end)

    return s


def sentences(paper: Paper) -> t.Sequence[Selection]:
    s = make_selector(paper)
    return [s(start, start + 1) for start in range(0, len(list(paper.sentences())))]


def text_to_selection(text: str, selections: t.Sequence[Selection]):
    selection_dict = {selection.original: selection for selection in selections}
    return selection_dict[text]


class Decontext(Selection):
    questions: Optional[t.Sequence[str]]
    out: str

    def __str__(self):
        return self.out


class Trace(BaseModel):
    components: t.Sequence[Union[str, Selection]]


T = t.TypeVar("T")


class Beam(GenericModel, t.Generic[T]):
    ...


def remove_lowest_perplexity(results: t.Sequence[tuple[str, float]]):
    drop = min(range(len(results)), key=lambda idx: results[idx][1])
    return list(results[0:drop]) + list(results[drop + 1 :])


def remove_highest_perplexity(results: t.Sequence[tuple[str, float]]):
    drop = max(range(len(results)), key=lambda idx: results[idx][1])
    return list(results[0:drop]) + list(results[drop + 1 :])
