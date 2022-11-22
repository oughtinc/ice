import re

from typing import Optional

from lxml import etree
from pydantic import BaseModel

from ice.kelvin.actions.base import Action
from ice.kelvin.models import Card


class Record(BaseModel):
    action: Optional[Action] = None
    card: Card

    def __str__(self):
        if not self.action:
            return str(self.card)
        return f"""{self.action}\n{self.card}"""


History = list[Record]


def shorten_repeated_elements(text):
    """
        Replace tags that occur more than once (as indicated by id) with just their id.
        Don't show their content or non-id parameters in subsequent occurrences.
        Note that the contents of tags may go over multiple lines.

        Example:
        >>> text = '''<card id="0UAqFzWsDK4FrUMp">(Initial card)</card>
    <action id="123" kind="AddReasoning">foo</action>
    <card id="hnX6bAgqnOvlFcg9">
    <row id="cJ4HQbNLJyw8cb7l" kind="text">foo</row>
    </card>
    <action id="123" kind="AddReasoning">bar</action>
    <card id="TtmsD6XrIQXByVAp">
    <row id="cJ4HQbNLJyw8cb7l" kind="text">foo</row>
    <row id="beeAITiANfBw6dzz" kind="text">bar</row>
    </card>
    '''
        >>> shorten_repeated_elements(text)

    <card id="0UAqFzWsDK4FrUMp">(Initial card)</card>
    <action id="123" kind="AddReasoning">foo</action>
    <card id="hnX6bAgqnOvlFcg9">
    <row id="cJ4HQbNLJyw8cb7l" kind="text">foo</row>
    </card>
    <action id="123" annotation="see above"/>
    <card id="TtmsD6XrIQXByVAp">
    <row id="cJ4HQbNLJyw8cb7l" annotation="see above" />
    <row id="beeAITiANfBw6dzz" kind="text">bar</row>
    </card>

    Approach: Iterate over all tags. If tag is repeated, replace it
    with a tag that has just the id, no params or contents

    """
    try:
        parser = etree.XMLParser(recover=True)
        tree = etree.fromstring(f"<root>{text}</root>", parser)
    except etree.XMLSyntaxError:
        return "Invalid XML"

    # Empty duplicate tags
    seen_ids = set()
    for tag in tree.iter():
        if "id" in tag.attrib:
            if tag.attrib["id"] in seen_ids:
                # remove all attributes except for id
                for attr in list(tag.attrib):
                    if attr != "id":
                        del tag.attrib[attr]
                tag.attrib["annotation"] = "see above"
                # remove any content inside the tag
                tag.text = None
                for child in list(tag):
                    tag.remove(child)
            else:
                seen_ids.add(tag.attrib["id"])

    # Shorten repeated sequences of id-only elements
    for tag in tree.iter():
        if len(tag.attrib) == 2 and "id" in tag.attrib and "annotation" in tag.attrib:
            # find the sequence of id-only elements
            sequence = [tag]
            next_tag = tag.getnext()
            while (
                next_tag is not None
                and len(next_tag.attrib) == 2
                and "id" in next_tag.attrib
                and "annotation" in next_tag.attrib
            ):
                sequence.append(next_tag)
                next_tag = next_tag.getnext()
            # replace the middle elements with a placeholder
            if len(sequence) > 2:
                for middle_tag in sequence[1:-1]:
                    middle_tag.tag = "placeholder"
                    for attr in list(middle_tag.attrib):
                        del middle_tag.attrib[attr]

    # convert to string
    result = etree.tostring(tree, encoding="unicode")

    # replace the placeholder with an ellipsis
    result = result.replace("<placeholder/>", "...")
    while "...\n..." in result:
        result = result.replace("...\n...", "...")

    # remove the root tag
    result = re.sub(r"<\/?root>", "", result)

    # add newline before <card>
    result = re.sub(r"(<card)", r"\n\1", result)
    result = result.strip()

    return result


def history_to_str(history: History) -> str:
    history_str = "\n".join(str(record) for record in history)
    history_str = shorten_repeated_elements(history_str)
    return history_str


if __name__ == "__main__":
    with open("session.txt") as f:
        text = f.read()
    print(shorten_repeated_elements(text))
