import asyncio
import re

from structlog import get_logger

from ice.agents.openai import OpenAIAgent
from ice.kelvin.actions.base import Action
from ice.kelvin.actions.base import ActionParam
from ice.kelvin.actions.elicit import ElicitSearchAction
from ice.kelvin.actions.elicit import ViewPaperAction
from ice.kelvin.actions.expand_collapse import ToggleAction
from ice.kelvin.actions.text import AddTextRowAction
from ice.kelvin.history import History
from ice.kelvin.history import history_to_str
from ice.kelvin.models import Frontier

log = get_logger()

SHORT_EXAMPLE_SESSION = """<card id="XfLEN0pThnXuYgjR">
<row id="35HyRrY03K6JBO94" kind="text">I'd like to know how robust research on creatine for cognition is.</row>
</card>
<action kind="FindPapers">What are the effects of creatine on cognition?</action>

<card id="beeAITiANfBw6dzz">
<row id="cMNgIvxWE2LCNuhQ" kind="paper" title="Effects of creatine supplementation on cognitive function of healthy individuals: A systematic review of randomized controlled trials" year="2018" has_full_text="True" is_expanded="false"/>
<row id="MWh4X42QYGWlWBUC" kind="paper" title="Cognitive effects of creatine ethyl ester supplementation" year="2009" has_full_text="False" is_expanded="false"/>
<row id="Wec5E36PJnfY3WRA" kind="paper" title="Creatine Supplementation and Cognitive Performance in Elderly Individuals" year="2007" has_full_text="False" is_expanded="false"/>
</card>
<action kind="AddReasoning">The first paper is a systematic review and the newest among the papers listed here.</action>

<card id="rgCukA3ABRGi4BWy">
<row id="cMNgIvxWE2LCNuhQ" annotation="see above"/>
...
<row id="Wec5E36PJnfY3WRA" annotation="see above"/>
<row id="aGe1QUPacM92RToU" kind="text">The first paper is a systematic review and the newest among the papers listed here.</row>
</card>
<action kind="ViewPaper">cMNgIvxWE2LCNuhQ: Effects of creatine supplementation on cognitive function of healthy individuals</action>"""

LONG_EXAMPLE_SESSION = (
    SHORT_EXAMPLE_SESSION
    + """

<card id="bhtNxpxCKIwAXK8L">
<row id="cMNgIvxWE2LCNuhQ" annotation="see above"/>
<row id="ihx82tYfyJ9dz5bL" kind="paper_section" title="Abstract" paper="cMNgIvxWE2LCNuhQ" is_expanded="true">Background and aims: Creatine is a supplement used by sportsmen to increase athletic performance by improving energy supply to muscle tissues. It is also an essential brain compound and some hypothesize that it aids cognition by improving energy supply and neuroprotection. Results: Six studies (281 individuals) met our inclusion criteria. Generally, there was evidence that short term memory and intelligence/reasoning may be improved by creatine administration. Findings suggest potential benefit for aging and stressed individuals. Since creatine is safe, future studies should include larger sample sizes.</row>
<row id="yIRz379dZ2j6hm7Z" kind="paper_section" title="1. Introduction" paper="cMNgIvxWE2LCNuhQ" is_expanded="false">Creatine is a naturally occurring compound that is synthesized from the amino acids arginine, glycin...</row>
<row id="JrpyaNdVearVZF6h" kind="paper_section" title="2. Methods" paper="cMNgIvxWE2LCNuhQ" is_expanded="false">The Preferred Reporting Items for Systematic reviews and Meta-Analyses (PRISMA) guidelines were adop...</row>
<row id="uTujJdxpuEHftxzD" kind="paper_section" title="2.1. Information sources" paper="cMNgIvxWE2LCNuhQ" is_expanded="false">"PubMed", "Science Direct" and Cochrane Central Register of Controlled trials were used for the iden...</row>
<row id="OU3Q0WjcTG9kxr2D" kind="paper_section" title="2.2. Data collection process and data items" paper="cMNgIvxWE2LCNuhQ" is_expanded="false">Data was extracted by two reviewers (KA, NS) and included the next fields: title, 1st author, year o...</row>
<row id="4R9L8kBJ8J1MFyws" kind="paper_section" title="2.3. Risk of bias in individual studies" paper="cMNgIvxWE2LCNuhQ" is_expanded="false">The Cochrane Collaboration's tool was used for the assessment of risk of bias (ROB) by two reviewers...</row>
<row id="n7H126ouNtiVIHSh" kind="paper_section" title="3.1. Search results" paper="cMNgIvxWE2LCNuhQ" is_expanded="false">The search resulted in 769 potentially eligible studies. After removal of duplicated studies, 715 st...</row>
<row id="5DQLLSfEnyFvzTc7" kind="paper_section" title="3.2. Characteristics of included studies and patients" paper="cMNgIvxWE2LCNuhQ" is_expanded="false">Six studies were included for qualitative synthesis, corresponding to 281 patients. Half studies too...</row>
<row id="LkIfFQAtP52x1hd8" kind="paper_section" title="3.3. Risk of bias" paper="cMNgIvxWE2LCNuhQ" is_expanded="false">In the Rae et al. study, which was independently assessed, we found the following: i) the cross-over...</row>
<row id="VMIt30DnPT9Xf90K" kind="paper_section" title="3.4. Results of individual studies" paper="cMNgIvxWE2LCNuhQ" is_expanded="false">3.4.1. Effects of creatine on cognition-For the assessment of creatine's effect on cognition, variou...</row>
</card>
<action kind="AddReasoning">The abstract says that "future studies should include larger sample sizes" which implies that the sample sizes are not very large.</action>

<card id="D3STN3SN5Va1lUzy">
<row id="cMNgIvxWE2LCNuhQ" annotation="see above"/>
...
<row id="VMIt30DnPT9Xf90K" annotation="see above"/>
<row id="Im7NU3CHBMuYwVbw" kind="text">The abstract says that "future studies should include larger sample sizes" which implies that the sample sizes are not very large.</row>
</card>
<action kind="AddReasoning">The risk of bias sections may contain more information about the robustness of the studies in the systematic review.</action>

<card id="P0DfCSnh9BO9RzHE">
<row id="cMNgIvxWE2LCNuhQ" annotation="see above"/>
...
<row id="Im7NU3CHBMuYwVbw" annotation="see above"/>
<row id="ia7BOJR3uOasbB13" kind="text">The risk of bias sections may contain more information about the robustness of the studies in the systematic review.</row>
</card>
<action kind="AddReasoning">The first risk of bias section is part of the methods, whereas the second one seems to be part of the results, so let's start with the second one.</action>

<card id="ymG0MKzbaGPOJBY1">
<row id="cMNgIvxWE2LCNuhQ" annotation="see above"/>
...
<row id="ia7BOJR3uOasbB13" annotation="see above"/>
<row id="qItJHoSCDE9Ypvnu" kind="text">The first risk of bias section is part of the methods, whereas the second one seems to be part of the results, so let's start with the second one.</row>
</card>
<action kind="Toggle">LkIfFQAtP52x1hd8: 3.3. Risk of bias</action>"""
)


def get_model_action(frontier: Frontier, history: History) -> Action:
    """
    v1: fixed commands
    """
    # 1. Compute prompt from frontier
    #    - We do need to know the history of the current card though

    history_str = history_to_str(history)

    prompt = f"""
You are an AI research assistant. You are helping a user do research. The user is trying to answer research questions by searching for papers, reading relevant sections, and writing down reasoning steps.

The user's workspace is a sequence of cards. At each point the user is looking at a single card. The user issues actions that operate on the current card and generate a new card.

Your goal is to find out what the user wants and help them accomplish their goal by suggesting helpful next actions. Whenever a new paper or card gets added or expanded, show your reasoning.

Available actions:
<action kind="FindPapers">[query]</action> runs a semantic search through about 200 million academic papers and gets the top results for the search term [query].
<action kind="AddReasoning">[thought]</action> use this to write down your thinking process and share information with the user.
<action kind="ViewPaper">[id]: [short paper title]</action> zoom in on a paper in the current card.
<action kind="Toggle">[id]: [short section title]</action> expand a section in the current card that has is_expanded="false".

Here's an example of a session:
========
{SHORT_EXAMPLE_SESSION}
========

Here's the current session:
========
{history_str}
========

What action would you like to run?<|endofprompt>

<action"""
    # 2. Get model response
    agent = OpenAIAgent(
        model="text-alpha-002-current",
    )
    # log.info("Running prompt", prompt=prompt)
    result_str = asyncio.run(agent.complete(prompt=prompt)).strip()
    if result_str:
        result_str = "<action " + result_str

    # log.info("Got result", result=result_str)

    # 3. Construct action from model response

    # extract the kind and params from the string
    match = re.match(r'<action kind="([^"]+)">([^<]+)</action>', result_str)
    if not match:
        raise ValueError(f"Invalid action string: {result_str}")

    kind, params_str = match.groups()

    # Possible response formats:

    if kind == "FindPapers":
        # "<action kind="FindPapers">[query]</action>"
        action = ElicitSearchAction(
            params=[
                ActionParam(
                    name="query", kind="TextParam", label="Query", value=params_str
                )
            ],
            label=f"Search papers: {params_str}",
        )
    elif kind == "AddReasoning":
        # "<action kind="AddReasoning">[thought]</action>"
        action = AddTextRowAction(
            params=[
                ActionParam(
                    name="row_text", kind="TextParam", label="Text", value=params_str
                )
            ],
            label=f"Add note: {params_str}",
        )
    elif kind == "ViewPaper":
        # "<action kind="ViewPaper">[id]: [short paper title]</action>"
        match = re.match(r"([^:]+): (.+)", params_str)
        if match:
            paper_id, title = match.groups()
        else:
            paper_id = params_str
            title = "(unknown title)"
            # raise ValueError(f"Invalid action string: {result_str}")
        action = ViewPaperAction(
            params=[
                ActionParam(
                    name="paper_id", kind="IdParam", label="Paper", value=paper_id
                )
            ],
            label=f"View paper: {title}",
        )
    elif kind == "Toggle":
        # "<action kind="Toggle">[id]: [short section title]</action>"
        match = re.match(r"([^:]+): (.+)", params_str)
        if match:
            section_id, title = match.groups()
        else:
            section_id = params_str
            title = "(unknown title)"
            # raise ValueError(f"Invalid action string: {result_str}")
        action = ToggleAction(
            params=[
                ActionParam(
                    name="section_id", kind="IdParam", label="Section", value=section_id
                )
            ],
            label=f"Toggle section: {title}",
        )
    else:
        raise ValueError(f"Invalid action kind: {kind}")

    return action
