from typing import Literal

from ice.kelvin.actions.base import Action
from ice.kelvin.actions.base import ActionParam
from ice.kelvin.models import Card
from ice.kelvin.models import Frontier
from ice.kelvin.models import HydratedPath
from ice.kelvin.models import PartialFrontier
from ice.kelvin.models import Path
from ice.kelvin.models import View


class CreatePathAction(Action):

    kind: Literal["CreatePathAction"] = "CreatePathAction"
    params: list[ActionParam] = [
        ActionParam(name="path_name", kind="TextParam", label="Name")
    ]
    label: str = "Create path"

    def execute(self, frontier: Frontier) -> PartialFrontier:
        new_card = Card(created_by_action=self)
        new_path = HydratedPath(
            label=self.params[0].value, head_card=new_card, view=View()
        )
        return PartialFrontier(paths={new_path.id: new_path}, focus_path_id=new_path.id)

    @classmethod
    def instantiate(cls, frontier: Frontier) -> list[Action]:
        return [cls()]


class SwitchPathAction(Action):

    kind: Literal["SwitchPathAction"] = "SwitchPathAction"
    params: list[ActionParam] = [
        ActionParam(name="path_id", kind="IdParam", label="Path ID")
    ]
    label: str = "Switch path"

    def execute(self, frontier: Frontier) -> PartialFrontier:
        path_id = self.params[0].value
        if path_id not in frontier.paths:
            raise ValueError(f"Path ID {path_id} not found in frontier.")
        return PartialFrontier(paths=frontier.paths, focus_path_id=path_id)

    @classmethod
    def instantiate(cls, frontier: Frontier) -> list[Action]:
        return [
            cls(
                params=[
                    ActionParam(
                        name="path_id",
                        kind="IdParam",
                        label="Path ID",
                        value=path_id,
                        readable_value=frontier.paths[path_id].label,
                    )
                ],
                label=f"Switch to path {frontier.paths[path_id].label}",
            )
            for path_id in frontier.paths
            if path_id != frontier.focus_path_id
        ]


class SaveElementToPathAction(Action):

    kind: Literal["SavePaper"] = "SavePaper"  # TODO
    params: list[ActionParam] = [
        ActionParam(name="element_id", kind="IdParam", label="Element ID"),
        ActionParam(name="path_id", kind="IdParam", label="Path ID"),
    ]
    label: str = "Save selection to path"

    def execute(self, frontier: Frontier) -> PartialFrontier:
        element_id = self.params[0].value
        if element_id == "SELECTED":
            elements = frontier.get_marked_rows()
        else:
            # Look up row by id
            rows = frontier.focus_path().rows()
            row = next((row for row in rows if row.id == element_id), None)
            if row is None:
                raise ValueError(f"Row ID {element_id} not found in frontier.")
            elements = [row]

        path_id = self.params[1].value
        if path_id not in frontier.paths:
            raise ValueError(f"Path ID {path_id} not found in frontier.")

        # Get the most recent card in the target path
        target_path = frontier.paths[path_id]
        target_card = target_path.head_card

        # Create a new card in the target path
        recorded_action = SaveElementToPathAction(
            params=[
                ActionParam(
                    name="element_id",
                    kind="IdParam",
                    label="Element ID",
                    value=elements[0].id,
                    readable_value=elements[0].readable_value(),
                ),
                ActionParam(
                    name="path_id",
                    kind="IdParam",
                    label="Path ID",
                    value=path_id,
                    readable_value=target_path.label,
                ),
            ],
            label=f"Save selection to path {target_path.label}",
        )

        new_card = Card(
            rows=target_card.rows + elements,
            prev_id=target_card.id,
            created_by_action=recorded_action,
        )

        # Update the target path
        new_target_path = target_path.update_head(
            new_head_card=new_card, new_view=View()
        )

        # Also create a new card in the current path
        current_path = frontier.focus_path()
        current_card = current_path.head_card
        new_current_card = Card(
            rows=current_card.rows,
            prev_id=current_card.id,
            created_by_action=recorded_action,
        )

        # Update the current path
        new_current_path = current_path.update_head(
            new_head_card=new_current_card, new_view=current_path.view
        )

        return PartialFrontier(
            focus_path_id=frontier.focus_path_id,
            paths={
                path_id: new_target_path,
                frontier.focus_path_id: new_current_path,
            },
        )

    @classmethod
    def instantiate(cls, frontier: Frontier) -> list[Action]:
        # Only show this action if there are marked rows
        if not frontier.get_marked_rows():
            return []
        return [
            cls(
                params=[
                    ActionParam(
                        name="element_id",
                        kind="IdParam",
                        label="Element",
                        value="SELECTED",
                    ),
                    ActionParam(
                        name="path_id",
                        kind="IdParam",
                        label="Path ID",
                        value=path_id,
                        readable_value=frontier.paths[path_id].label,
                    ),
                ],
                label=f"Save selection to path {frontier.paths[path_id].label}",
            )
            for path_id in frontier.paths
            if path_id != frontier.focus_path_id
        ]
