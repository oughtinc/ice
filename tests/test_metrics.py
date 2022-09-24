import numpy as np

from pytest import mark

from ice.metrics.base import reduce_scores_dict
from ice.metrics.base import Sample
from ice.metrics.gold_paragraphs import get_gold_paragraph_df
from ice.metrics.nubia import Nubia
from ice.metrics.rouge import Rouge


def test_reduce_scores_to_single_value():
    scores = [dict(metric_a=0.1, metric_b=0.3), dict(metric_a=0.2, metric_b=0.4)]
    target_reduced_scores = dict(metric_a=0.15, metric_b=0.35)
    calculated_reduced_scores = reduce_scores_dict(scores, lambda x: sum(x) / len(x))
    for k, v in target_reduced_scores.items():
        assert k in calculated_reduced_scores
        assert np.isclose(calculated_reduced_scores[k], v)


@mark.anyio
async def test_rouge_basic_precision():
    samples = [
        Sample(left=["I can haz cheeseburger"], right=["I make cats haz cheeseburger"])
    ]
    scores = await Rouge().compute(samples)

    # Basic sanity check
    rouge_1_p = scores[0].dict()["rouge_1"]["p"]
    rouge_2_p = scores[0].dict()["rouge_2"]["p"]

    assert rouge_1_p == 3 / 4
    assert rouge_2_p == 1 / 3


@mark.anyio
@mark.parametrize(
    "left,right,expected_result",
    [
        (["subsequence"], ["sequence including subsequence"], 1 / 3),
        (["sequence including subsequence"], ["subsequence"], 1),
        (["sequence including subsequence"], ["sequence", "other random crap"], 0.25),
    ],
)
async def test_rouge_recall(left, right, expected_result):
    samples = [Sample(left=left, right=right)]
    scores = await Rouge().compute(samples)

    rouge_l_r = scores[0].dict()["rouge_l"]["r"]

    assert rouge_l_r == expected_result


@mark.anyio
async def test_rouge_multiple_hypotheses_and_references_matches_single_score_when_inputs_are_identical():
    sample_single = [
        Sample(left=["I can haz cheeseburger"], right=["I make cats haz cheeseburger"])
    ]
    scores_single = await Rouge().compute(sample_single)

    samples_repeated = [
        Sample(
            left=["I can haz cheeseburger", "I can haz cheeseburger"],
            right=["I make cats haz cheeseburger", "I make cats haz cheeseburger"],
        )
    ]
    scores_repeated = await Rouge().compute(samples_repeated)

    assert scores_single == scores_repeated


@mark.skip(reason="Requires OUGHT_INFERENCE_API_KEY")
@mark.slow
@mark.anyio
async def test_nubia():
    m = Nubia()
    sample_single = [
        Sample(left=["I can haz cheeseburger"], right=["I cannot haz cheeseburger"])
    ]
    resp = await m.compute(sample_single)
    assert len(resp) == 1 and len(resp[0]) == 1
    # These are strongly contradictory & the model is deterministic
    assert resp[0][0].contradiction > 0.99


@mark.skip(reason="Parses all PDFs - very slow")
@mark.slow
@mark.anyio
async def test_gold_paragraphs():
    gold_paragraphs_df, id_to_paragraph = get_gold_paragraph_df("placebo")

    assert "quote" in gold_paragraphs_df.columns
    assert "paragraph" in gold_paragraphs_df.columns
    assert "paragraph_id" in gold_paragraphs_df.columns

    assert len(gold_paragraphs_df) > 20

    for _, paragraph_id in gold_paragraphs_df["paragraph_id"].iteritems():
        paragraph = id_to_paragraph[paragraph_id]
        assert not paragraph.is_empty()
