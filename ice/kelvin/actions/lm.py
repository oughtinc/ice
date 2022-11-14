import asyncio

from typing import Literal

from structlog import get_logger

from ice.agents.openai import OpenAIAgent
from ice.kelvin.actions.base import Action
from ice.kelvin.actions.base import ActionParam
from ice.kelvin.models import Card
from ice.kelvin.models import Frontier
from ice.kelvin.models import PartialFrontier
from ice.kelvin.models import View
from ice.kelvin.rows import TextRow

log = get_logger()


class GenerationAction(Action):

    kind: Literal["GenerationAction"] = "GenerationAction"
    params: list[ActionParam] = [
        ActionParam(name="context", kind="TextParam", label="Context"),
        ActionParam(name="command", kind="TextParam", label="Command"),
    ]
    label: str = "Run language model command on selection"

    def execute(self, frontier: Frontier) -> PartialFrontier:
        context = self.params[0].value
        command = self.params[1].value
        agent = OpenAIAgent()

        if context == "NO_CONTEXT":
            prompt = command
        else:
            prompt = f'''Context:
"""
{context}
"""

Command: {command}

Result:

-'''
        log.info("Running prompt", prompt=prompt)
        result_str = asyncio.run(agent.complete(prompt=prompt)).strip()
        log.info("result", result=result_str)
        if "\n\n" in result_str:
            results = result_str.split("\n\n")
        else:
            results = result_str.split("\n")
        old_card = frontier.focus_path_head()
        new_rows = [TextRow(text=result.lstrip(" -*")) for result in results]
        new_card = Card(rows=new_rows, prev_id=old_card.id)

        new_frontier = frontier.update_focus_path_head(
            new_head_card=new_card,
            new_view=View(
                focused_row_index=len(new_rows) - 1,
            ),
        )
        return new_frontier

    @classmethod
    def instantiate(cls, frontier: Frontier) -> list[Action]:
        actions: list[Action] = []

        row_kinds = frontier.get_marked_row_kinds()
        if row_kinds == {"Text"}:
            marked_rows = frontier.get_marked_rows()
            lm_action = cls(
                label=f"Run language model command on {len(marked_rows)} rows",
                params=[
                    ActionParam(
                        name="context",
                        kind="TextParam",
                        label="Context",
                        value="\n\n".join([f"- {row.text}" for row in marked_rows]),
                    ),
                    ActionParam(name="command", kind="TextParam", label="Command"),
                ],
            )
            show_more_action = cls(
                label="Generate more bullets like this",
                params=[
                    ActionParam(
                        name="context",
                        kind="TextParam",
                        label="Context",
                        value="\n\n".join([f"- {row.text}" for row in marked_rows]),
                    ),
                    ActionParam(
                        name="command",
                        kind="TextParam",
                        label="Command",
                        value="Generate more examples of the kind in the context.",
                    ),
                ],
            )
            actions += [lm_action, show_more_action]
        else:
            lm_action = cls(
                label="Run language model command",
                params=[
                    ActionParam(
                        name="context",
                        kind="TextParam",
                        label="Context",
                        value="NO_CONTEXT",
                    ),
                    ActionParam(name="command", kind="TextParam", label="Command"),
                ],
            )
            actions += [lm_action]
        return actions
