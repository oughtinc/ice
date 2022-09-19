from typing import Type

from ice.recipe import Recipe

from .adherence_keyword_baseline import AdherenceKeywordBaseline
from .adherence_simple import AdherenceSimpleInstruct
from .adherence_tfew_paragraph import AdherenceParagraphTfew
from .all_quotes import AllQuotesRecipe
from .blinding_dynamic import BlindingDynamic
from .comparisons_qa import ComparisonsQA
from .evaluate_result import EvaluateResult
from .evaluate_results import EvaluateResults
from .experiment_arms import ExperimentArms
from .finalN import FinalN
from .funnel_simple import FunnelSimple
from .placebo_description import PlaceboDescriptionInstruct
from .placebo_dialogs import PlaceboDialogs
from .placebo_keyword_baseline import PlaceboKeywordBaseline
from .placebo_simple import PlaceboSimpleInstruct
from .placebo_tree import PlaceboTree
from .rank_paragraphs import RankParagraphs
from .subrecipe_example import ExampleMetaRecipe
from .tutorial_amplification import AmplifiedQA
from .tutorial_debate import DebateRecipe
from .tutorial_hello import HelloWorld
from .tutorial_paperqa import PaperQA
from .tutorial_qa import QA


def get_recipe_classes() -> list[Type[Recipe]]:
    return [
        AdherenceKeywordBaseline,
        AdherenceParagraphTfew,
        AdherenceSimpleInstruct,
        AllQuotesRecipe,
        AmplifiedQA,
        BlindingDynamic,
        ComparisonsQA,
        DebateRecipe,
        EvaluateResult,
        EvaluateResults,
        ExampleMetaRecipe,
        ExperimentArms,
        FunnelSimple,
        HelloWorld,
        PaperQA,
        PlaceboDescriptionInstruct,
        PlaceboDialogs,
        PlaceboKeywordBaseline,
        PlaceboSimpleInstruct,
        PlaceboTree,
        QA,
        RankParagraphs,
        FinalN,
    ]
