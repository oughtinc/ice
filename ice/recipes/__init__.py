from typing import Type

from ice.recipe import Recipe

from .adherence_keyword_baseline import AdherenceKeywordBaseline
from .adherence_simple import AdherenceSimpleInstruct
from .adherence_tfew_paragraph import AdherenceParagraphTfew
from .all_quotes import AllQuotesRecipe
from .blinding_dynamic import BlindingDynamic
from .experiments_and_arms.recipes.name_experiments import NameExperiments
from .experiments_and_arms.recipes.experiments_and_arms import ExperimentsAndArms
from .comparisons_qa import ComparisonsQA
from .evaluate_result import EvaluateResult
from .evaluate_results import EvaluateResults
from .experiment_arms import ExperimentArms
from .funnel_simple import FunnelSimple
from .placebo_description import PlaceboDescriptionInstruct
from .program_search.nodes.decontext.decontextualize import PaperDecontext
from .program_search.nodes.select.select import PaperSelect
from .program_search.example import DecontextAndSelect
from .placebo_dialogs import PlaceboDialogs
from .placebo_keyword_baseline import PlaceboKeywordBaseline
from .placebo_simple import PlaceboSimpleInstruct
from .placebo_tree import PlaceboTree
from .rank_paragraphs import RankParagraphs
from .subrecipe_example import ExampleMetaRecipe


def get_recipe_classes() -> list[Type[Recipe]]:
    return [
        AdherenceKeywordBaseline,
        AdherenceParagraphTfew,
        AdherenceSimpleInstruct,
        AllQuotesRecipe,
        BlindingDynamic,
        ComparisonsQA,
        NameExperiments,
        ExperimentsAndArms,
        EvaluateResult,
        EvaluateResults,
        ExampleMetaRecipe,
        PaperDecontext,
        PaperSelect,
        DecontextAndSelect,
        ExperimentArms,
        FunnelSimple,
        PlaceboDescriptionInstruct,
        PlaceboDialogs,
        PlaceboKeywordBaseline,
        PlaceboSimpleInstruct,
        PlaceboTree,
        RankParagraphs,
    ]
