import asyncio

from typing import Literal

from structlog import get_logger

from ice.agents.openai import OpenAIAgent
from ice.kelvin.actions.base import Action
from ice.kelvin.actions.base import ActionParam
from ice.kelvin.cards.base import Card
from ice.kelvin.cards.text import TextCard
from ice.kelvin.cards.text import TextRow
from ice.kelvin.view import CardView
from ice.kelvin.view import CardWithView

log = get_logger()


class GenerationAction(Action):

    kind: Literal["GenerationAction"] = "GenerationAction"
    params: list[ActionParam] = [
        ActionParam(name="context", kind="TextParam", label="Context"),
        ActionParam(name="command", kind="TextParam", label="Command"),
    ]
    label: str = "Run language model command on selection"

    def validate_input(self, card: Card) -> None:
        pass

    def execute(self, card: Card) -> CardWithView:
        context = self.params[0].value
        command = self.params[1].value
        new_row = TextRow(text=f"Result of '{command}' on '{context}'")
        agent = OpenAIAgent()
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
        new_rows = [TextRow(text=result.lstrip(" -*")) for result in results]
        new_card = TextCard(rows=new_rows)
        new_view = CardView(card_id=new_card.id, selected_rows={new_row.id: True})
        return CardWithView(card=new_card, view=new_view)

    @classmethod
    def instantiate(cls, card_with_view: CardWithView) -> list[Action]:
        actions: list[Action] = []
        if card_with_view.card.kind == "TextCard":
            marked_rows = card_with_view.get_marked_rows()
            if marked_rows:
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
        return actions
