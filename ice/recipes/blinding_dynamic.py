"""
Papers that explicitly mention blinding of participants:
- awasthi-2013.pdf
- cheng-2020.pdf
- deutschmann-2019.pdf
- dicko-2008.pdf
- keenan-2018.pdf
- matangila-2015.pdf
- miguel-kremer-2004.pdf
- routledge-2006.pdf
- smithuis-2013.pdf

Papers that explicitly mention blinding of personnel:
- awasthi-2013.pdf
- bassi-2018.pdf (?)
- deutschmann-2019.pdf
- dicko-2008.pdf
- keenan-2018.pdf
- matangila-2015.pdf
- nyqvist-218.pdf
- routledge-2006.pdf
- vittengl-2009.pdf
"""
import itertools
from typing import Any
from typing import Literal
from typing import Optional
from typing import Union

import rich
import tqdm
from pydantic import BaseModel
from rich.panel import Panel
from thefuzz import fuzz

from ice.evaluation.evaluate_recipe_result import RecipeResult
from ice.metrics.gold_standards import get_gold_standards
from ice.metrics.gold_standards import GoldStandard
from ice.metrics.gold_standards import list_experiments
from ice.paper import Paper
from ice.paper import Paragraph
from ice.recipe import Recipe

# from rich.pretty import pprint

Group = Union[Literal["participants"], Literal["personnel"]]


def flatten(xs):
    return itertools.chain(*xs)


def quote(s: str):
    return f'"{s}"'


def sort_by_recall(gold_items: list[str], test_items: list[str]):
    test_string = " ".join(test_items)
    recalled_items = [
        gold_item
        for gold_item in gold_items
        if fuzz.partial_ratio(gold_item, test_string) > 95
    ]
    # for gold_item in gold_items:
    #     print(gold_item, fuzz.partial_ratio(gold_item, test_string))
    missed_items = [
        gold_item for gold_item in gold_items if gold_item not in recalled_items
    ]
    return recalled_items, missed_items


def get_blinding_gold_standards(
    *,
    paper: Paper,
    group: Group,
    explicitness: Union[Literal["explicit"], Literal["full"]] = "explicit",
    intervention: str,
) -> GoldStandard:
    question_short_name = f"blinding_{group}_{explicitness}"
    gold_standards = get_gold_standards(
        document_id=paper.document_id,
        question_short_name=question_short_name,
        experiment=intervention,
    )
    # if not gold_standards:
    #     fake_gold_standard = GoldStandard(
    #         document_id=paper.document_id,
    #         question_short_name=question_short_name,
    #         experiment=intervention,
    #         answer="",
    #         quotes=["bla"],
    #     )
    #     return fake_gold_standard
    assert len(gold_standards) == 1, gold_standards
    return gold_standards[0]


class InterventionResult(BaseModel):
    document_id: str
    question_short_name: str
    experiment: str
    answer: Optional[str]
    quotes: list[str]


class ParagraphResult(BaseModel):
    quotes: list[str]
    paragraph: Paragraph


PARTICIPANTS_CONTEXT = """Instructions for each paragraph:

What does the paragraph say explicitly about whether the participants (i.e. the people who received the intervention) were blinded to whether they were in the treatment or control group?

Include all relevant quotes:
- Everything the study explicitly says about whether participants were blinded. If the paper says that the experiment was "open label", that means participants knew whether they were in the treatment or control group. So, the experiment was not blinded.
- All efforts that the research team made to prevent participants from figuring out whether they were in the treatment or control group, e.g.: (a) the researchers didn’t tell the control group about the intervention, (b) placebos that looked the same as the real drug were used.

If the paragraph does not say anything about whether participants were blinded, say "n/a".

###

Paragraph: Between the 26th and 29th of April 1998, all households in the intervention villages received a number of Insecticide-treated bed nets (ITNs), according to the number of family members and were instructed explicitly about the correct use of the nets (Figure 2). Households in the control villages received identical-looking bed nets without insecticide treatment. More than 5000 ITN were distributed.

Quotes from paragraph that say whether the participants in the "Insecticide-treated bed nets (ITN)" intervention were blinded to allocation:
"Households in the control villages received identical-looking bed nets without insecticide treatment."

###

Paragraph: Between the 26th and 29th of April 1998, all households in the intervention villages received a number of Insecticide-treated bed nets (ITNs), according to the number of family members and were instructed explicitly about the correct use of the nets (Figure 2). Households in the control villages received identical-looking bed nets without insecticide treatment. More than 5000 ITN were distributed.

Quotes from paragraph that say whether the participants in the "meclizine" intervention were blinded to allocation:
n/a

###

Paragraph: The study was an open randomized controlled clinical trial. After a census of the village population, subjects in the target age group were screened for inclusion and exclusion criteria. Subjects who met inclusion and exclusion criteria were randomized either to receive two intermittent preventive treatments with standard recommended treatment doses of SP or no intermittent preventive treatment.

Quotes from paragraph that say whether the participants in the "intermittent preventive malaria treatment (IPT)" intervention with sulphadoxine pyrimethamine (SP) were blinded to allocation:
"The study was an open randomized controlled clinical trial."
"Subjects who met inclusion and exclusion criteria were randomized either to receive two intermittent preventive treatments with standard recommended treatment doses of SP or no intermittent preventive treatment."

###

Paragraph: To facilitate community-based treatment of malaria with the assigned regimen (artemether-lumefantrine or dihydroartemisinin-piperaquine), and to ensure that children received the correct regimen if they attended at health centres in the study area, ID cards were colour-coded according to intervention group and labelled with the regimen to be used for case management. The study was therefore open-label with respect to the regimen used for case management but blinded with respect to whether seasonal malaria chemoprevention was active or placebo (members of the research team from KNUST/CGHR and LSHTM were aware of the allocation, but those who administered the SMC, and mothers/children were blinded).

Quotes from paragraph that say whether the participants in the "short-acting ACT for case management of malaria (artemether-lumefantrine, AL) plus placebo SMC" intervention were blinded to allocation:
"The study was therefore open-label with respect to the regimen used for case management but blinded with respect to whether seasonal malaria chemoprevention was active or placebo (members of the research team from KNUST/CGHR and LSHTM were aware of the allocation, but those who administered the SMC, and mothers/children were blinded)."

###

Paragraph: To facilitate community-based treatment of malaria with the assigned regimen (artemether-lumefantrine or dihydroartemisinin-piperaquine), and to ensure that children received the correct regimen if they attended at health centres in the study area, ID cards were colour-coded according to intervention group and labelled with the regimen to be used for case management. The study was therefore open-label with respect to the regimen used for case management but blinded with respect to whether seasonal malaria chemoprevention was active or placebo (members of the research team from KNUST/CGHR and LSHTM were aware of the allocation, but those who administered the SMC, and mothers/children were blinded).

Quotes from paragraph that say whether the participants in the "finasteride" intervention were blinded to allocation:
n/a

###

Paragraph: In India, the Integrated Child Development Service (ICDS) maintains a network of child-care centres, caring for children up to age 6 years and off ering the potential to deliver simple health interventions. In rural Uttar Pradesh in north India, our plans to use the ICDS infrastructure for a large cluster-randomised trial of the eff ects of 6-monthly deworming with albendazole on pre-school child mortality were revised into plans for a factorial trial that would also evaluate the eff ects on mortality of enhancing vitamin A coverage. This 5-year trial of Deworming and Enhanced Vitamin A supple mentation (DEVTA) in 1 million pre-school children was larger than all other vitamin A trials combined. Its primary aim was to assess eff ects of a standard periodic treatment regimen on mortality at ages 1·0–6·0 years.

Quotes from paragraph that say whether the participants in the "6-monthly vitamin A" intervention were blinded to allocation:
n/a

###

"""

PERSONNEL_CONTEXT = """Instructions for each paragraph:

What does the paper say explicitly about whether the personnel (i.e. the people who carried out the intervention) were blinded to whether the participants were in the treatment or control group?

Include all relevant quotes:
- Everything the study explicitly says about whether personnel were blinded. If the paper says that the experiment was "open label", that means personnel knew whether participants were in the treatment or control group. So, the experiment was not blinded. We want to know about blinding of all personnel, including personnel who administered the intervention and personnel who collected data.
- All efforts that the research team made to prevent personnel from figuring out whether participants were in the treatment or control group. E.g. placebos that looked the same as the real drug were used, and personnel didn’t know which was the placebo.

If the paragraph does not say anything about whether participants were blinded, say "n/a".

###

Paragraph: Between the 26th and 29th of April 1998, all households in the intervention villages received a number of Insecticide-treated bed nets (ITNs), according to the number of family members and were instructed explicitly about the correct use of the nets (Figure 2). Households in the control villages received identical-looking bed nets without insecticide treatment. More than 5000 ITN were distributed.

Quotes from paragraph that say whether the personnel in the "Insecticide-treated bed nets (ITN)" intervention were blinded to allocation:
n/a

###

Paragraph: The study was an open randomized controlled clinical trial. Some study personnel knew which participants were in the treatment group. After a census of the village population, subjects in the target age group were screened for inclusion and exclusion criteria. Subjects who met inclusion and exclusion criteria were randomized either to receive two intermittent preventive treatments with standard recommended treatment doses of SP or no intermittent preventive treatment.

Quotes from paragraph that say whether the personnel in the "intermittent preventive malaria treatment (IPT)" intervention with sulphadoxine pyrimethamine (SP) were blinded to allocation:
"The study was an open randomized controlled clinical trial."
"Some study personnel knew which participants were in the treatment group."

###

Paragraph: In India, the Integrated Child Development Service (ICDS) maintains a network of child-care centres, caring for children up to age 6 years and off ering the potential to deliver simple health interventions. In rural Uttar Pradesh in north India, our plans to use the ICDS infrastructure for a large cluster-randomised trial of the eff ects of 6-monthly deworming with albendazole on pre-school child mortality were revised into plans for a factorial trial that would also evaluate the eff ects on mortality of enhancing vitamin A coverage. This 5-year trial of Deworming and Enhanced Vitamin A supple mentation (DEVTA) in 1 million pre-school children was larger than all other vitamin A trials combined. Its primary aim was to assess eff ects of a standard periodic treatment regimen on mortality at ages 1·0–6·0 years.

Quotes from paragraph that say whether the personnel in the "6-monthly vitamin A" intervention were blinded to allocation:
n/a

###

Paragraph: To facilitate community-based treatment of malaria with the assigned regimen (artemether-lumefantrine or dihydroartemisinin-piperaquine), and to ensure that children received the correct regimen if they attended at health centres in the study area, ID cards were colour-coded according to intervention group and labelled with the regimen to be used for case management. The study was therefore open-label with respect to the regimen used for case management but blinded with respect to whether seasonal malaria chemoprevention was active or placebo (members of the research team from KNUST/CGHR and LSHTM were aware of the allocation, but those who administered the SMC, and mothers/children were blinded).

Quotes from paragraph that say whether the personnel in the "short-acting ACT for case management of malaria (artemether-lumefantrine, AL) plus placebo SMC" intervention were blinded to allocation:
"The study was therefore open-label with respect to the regimen used for case management but blinded with respect to whether seasonal malaria chemoprevention was active or placebo (members of the research team from KNUST/CGHR and LSHTM were aware of the allocation, but those who administered the SMC, and mothers/children were blinded)."

###

Paragraph: "This was an open-label, randomised controlled trial enrolling asymptomatic schoolchildren and investigating the efficacy of IPTsc with sulfadoxine/pyrimethamine (SP) or SP combined with piperaquine (PQ) on anaemia and malaria morbidity in Congolese schoolchildren. The trial was composed of three treatment arms: SP monotherapy; SP combined with PQ (SP/PQ); and no antima- larial treatment (control). The study was conducted in Mokali health area, a semi-rural area of Kinshasa, Democratic Republic of the Congo (DRC). Malaria transmission is intense and perennial in this region, with two seasonal peaks (March–May and November–December) [19,20]."

Quotes from paragraph that say whether the participants in the "sulfadoxine/pyrimethamine" intervention were blinded to allocation:
"This was an open-label, randomised controlled trial enrolling asymptomatic schoolchildren and investigating the efficacy of IPTsc with sulfadoxine/pyrimethamine (SP) or SP combined with piperaquine (PQ) on anaemia and malaria morbidity in Congolese schoolchildren."

###

"""


def parse_quotes(s: str, ignore="n/a"):
    return [
        clean_line
        for line in s.split("\n")
        if (clean_line := line.strip('"\n ')) and clean_line != ignore
    ]


def make_paragraph_prompt(paragraph: Paragraph, intervention: str, group: Group) -> str:
    context = PARTICIPANTS_CONTEXT if group == "participants" else PERSONNEL_CONTEXT
    question = f"""Paragraph: {str(paragraph)}

Quotes from paragraph that say whether the {group} in the "{intervention}" intervention were blinded to allocation:"""
    return context + question


def make_followup_paragraph_prompt(
    paragraph: Paragraph, intervention: str, group: Group, answer: str
) -> str:
    prev_prompt = make_paragraph_prompt(paragraph, intervention, group)
    new_context = f"{prev_prompt} {answer}\n\n"
    new_question = f"""Other quotes from this paragraph relevant to whether the {group} in the "{intervention}" intervention were blinded to allocation:"""
    return new_context + new_question


class BlindingDynamic(Recipe):
    async def interventions(self, paper: Paper) -> list[str]:
        return list_experiments(document_id=paper.document_id)

    async def blinding_by_paragraph(
        self,
        paragraph: Paragraph,
        intervention: str,
        group: Group,
        gold_standard: GoldStandard,
        ask_followup: bool = False,
    ) -> ParagraphResult:
        """
        Does this paragraph state that [group] is blinded wrt
        [intervention]? Return an answer supported by a quote.
        """
        prompt = make_paragraph_prompt(paragraph, intervention, group)
        raw_quotes = await self.agent().complete(prompt=prompt)
        quotes = parse_quotes(raw_quotes, ignore="n/a")
        if quotes and ask_followup:
            followup_prompt = make_followup_paragraph_prompt(
                paragraph, intervention, group, raw_quotes
            )
            followup_quotes = await self.agent().complete(
                prompt=followup_prompt,
            )
            lines = parse_quotes(followup_quotes, ignore="n/a")
            quotes += lines
        for gold_quote in gold_standard.quotes:
            if gold_quote in str(paragraph):
                quotes_string = " ".join(quotes)
                if gold_quote not in quotes_string:
                    rich.print(
                        Panel(f"{prompt} {quotes_string}\n\nGold quote: {gold_quote}")
                    )
        # rich.print(Panel(f"{question} {quotes}"))
        return ParagraphResult(quotes=quotes, paragraph=paragraph)

    async def combine_paragraph_results(
        self,
        paper: Paper,
        paragraph_results: list[ParagraphResult],
        intervention: str,
        group: Group,
    ) -> InterventionResult:
        """
        Summarize whether [group] was blinded wrt [intervention] based on
        paragraph-level results.
        """
        return InterventionResult(
            document_id=paper.document_id,
            question_short_name=f"blinding_{group}_explicit",
            experiment=intervention,
            answer=None,
            quotes=list(set(flatten(result.quotes for result in paragraph_results))),
        )

    async def blinding_for_intervention(
        self, paper: Paper, intervention: str
    ) -> dict[Group, dict[str, Any]]:
        """
        For both participants and personnel, summarize whether they were
        blinded wrt [intervention].
        """
        results_by_group = {}
        groups: tuple[Group, Group] = ("participants", "personnel")
        for group in groups:
            gold_standard = get_blinding_gold_standards(
                paper=paper, group=group, intervention=intervention
            )
            paragraph_results = []
            for paragraph in tqdm.tqdm(paper.paragraphs):
                result = await self.blinding_by_paragraph(
                    paragraph, intervention, group, gold_standard=gold_standard
                )
                paragraph_results.append(result)
            group_results = await self.combine_paragraph_results(
                paper, paragraph_results, intervention, group
            )
            comparison = {
                "actual": group_results,
                "gold": gold_standard,
            }
            # Quick recall stats
            # pprint(comparison)
            recalled_quotes, missed_quotes = sort_by_recall(
                gold_standard.quotes, group_results.quotes
            )
            print(
                f"Recall for {paper.document_id} - {intervention} - {group}: {len(recalled_quotes)} / {len(gold_standard.quotes)} (with {len(group_results.quotes)} results)"
            )
            if missed_quotes:
                print(f"Missed quotes: {', '.join(quote(q) for q in missed_quotes)}")
            results_by_group[group] = comparison
        return results_by_group

    async def run(self, paper: Paper):
        """
        For each intervention, summarize how it was blinded.
        """
        results_by_intervention: dict[str, dict[Group, dict[str, Any]]] = {}
        interventions = await self.interventions(paper)
        for intervention in interventions:
            results_by_intervention[
                intervention
            ] = await self.blinding_for_intervention(paper, intervention)

        recipe_results: list[RecipeResult] = []
        for intervention in interventions:
            for group in results_by_intervention[intervention]:
                if group == "participants":
                    continue
                result: InterventionResult = results_by_intervention[intervention][
                    group
                ]["actual"]
                recipe_results.append(
                    RecipeResult(
                        document_id=result.document_id,
                        question_short_name=result.question_short_name,
                        experiment=result.experiment,
                        result=result,
                        excerpts=result.quotes,
                    )
                )
        self.maybe_add_to_results(recipe_results)
        return recipe_results
