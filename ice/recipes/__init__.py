from typing import Type

from .adherence_keyword_baseline import AdherenceKeywordBaseline
from .adherence_simple import AdherenceSimpleInstruct
from .adherence_tfew_paragraph import AdherenceParagraphTfew
from .all_quotes import AllQuotesRecipe
from .blinding_dynamic import BlindingDynamic
from .comparisons_qa import ComparisonsQA
from .evaluate_result import EvaluateResult
from .evaluate_results import EvaluateResults
from .experiment_arms import ExperimentArms
from .experiments_and_arms.recipes.experiments_and_arms import ExperimentsAndArms
from .experiments_and_arms.recipes.name_experiments import NameExperiments
from .funnel_simple import FunnelSimple
from .placebo_description import PlaceboDescriptionInstruct
from .placebo_dialogs import PlaceboDialogs
from .placebo_keyword_baseline import PlaceboKeywordBaseline
from .placebo_simple import PlaceboSimpleInstruct
from .placebo_tree import PlaceboTree
from .program_search.nodes.decontext.decontextualize import PaperDecontext
from .rank_paragraphs import RankParagraphs
from .subrecipe_example import ExampleMetaRecipe
from ice.recipe import Recipe


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
        ExperimentArms,
        FunnelSimple,
        PlaceboDescriptionInstruct,
        PlaceboDialogs,
        PlaceboKeywordBaseline,
        PlaceboSimpleInstruct,
        PlaceboTree,
        RankParagraphs,
    ]
