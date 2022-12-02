from typing import Literal

from structlog import get_logger

from ice.kelvin.actions.base import Action
from ice.kelvin.actions.base import ActionParam
from ice.kelvin.actions.base import update_row_in_frontier
from ice.kelvin.models import Frontier
from ice.kelvin.models import PartialFrontier
from ice.kelvin.rows import Row

log = get_logger()


class ToggleAction(Action):
    kind: Literal["Toggle"] = "Toggle"
    params: list[ActionParam] = [
        ActionParam(name="row_id", kind="IdParam", label="Row Id"),
    ]
    label: str = "toggle"

    @classmethod
    def instantiate(cls, frontier: Frontier) -> list[Action]:
        marked_rows = frontier.get_marked_rows()
        actions: list[Action] = []
        for row in marked_rows:
            log.info(
                "ExpandCollapse.instantiate", is_expanded=hasattr(row, "is_expanded")
            )
            if hasattr(row, "is_expanded"):
                action_label = "Collapse" if row.is_expanded else "Expand"
                actions.append(
                    cls(
                        label=action_label,
                        params=[
                            ActionParam(
                                name="row_id",
                                kind="IdParam",
                                label="Row Id",
                                value=row.id,
                                readable_value=row.readable_value(),
                            )
                        ],
                    )
                )
        return actions

    def execute(self, frontier: Frontier) -> PartialFrontier:
        def toggle_row(row: Row) -> Row:
            _row = row.copy()
            _row.is_expanded = not _row.is_expanded
            return _row

        new_frontier = update_row_in_frontier(
            frontier=frontier,
            row_id=self.params[0].value,
            update_fn=toggle_row,
            action=self,
        )
        return new_frontier
