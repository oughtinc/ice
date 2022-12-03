from typing import Type

from ice.recipe import Recipe

from .all_quotes import AllQuotesRecipe
from .blinding_dynamic import BlindingDynamic
from .comparisons_qa import ComparisonsQA
from .evaluate_result import EvaluateResult
from .evaluate_results import EvaluateResults
from .experiment_arms import ExperimentArms
from .experiments_and_arms.recipes.experiments_and_arms import ExperimentsAndArms
from .experiments_and_arms.recipes.name_experiments import NameExperiments
from .funnel_simple import FunnelSimple
from .program_search.nodes.decontext.decontextualize import PaperDecontext
from .rank_paragraphs import RankParagraphs
from .subrecipe_example import ExampleMetaRecipe


def get_recipe_classes() -> list[Type[Recipe]]:
    return [
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
        RankParagraphs,
    ]
