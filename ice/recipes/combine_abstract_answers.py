from ice.recipe import recipe
from ice.recipes.abstract_qa import Abstract
from ice.recipes.abstract_qa import DEFAULT_ABSTRACTS


def make_prompt(question: str, abstracts: list[Abstract], answers: list[str]) -> str:
    abstract_answers_str = "\n\n".join(
        [
            f"Title B{i}: {abstract.title}\nAbstract B{i}: {abstract.text}\nAnswer B{i}: {answer}"
            for i, (abstract, answer) in enumerate(zip(abstracts, answers), start=1)
        ]
    )

    return f"""For each set of abstracts, combine the abstract-wise answers to answer the question. Provide references to the original answers to support each claim in your combined answer.

###

Question A: What is IL-13?

Abstract A1: Interleukin 13 (IL-13) is a recently described protein secreted by activated T cells which is a potent in vitro modulator of human monocyte and B-cell functions. The data, reviewed here by Gerard Zurawski and Jan de Vries, shows that IL-13 shares biological activities with IL-4, their genes are closely linked in both the human and mouse genomes, and there is sequence homology between IL-13 and IL-4 proteins. Although the cloned IL-4 receptor protein (IL-4R) does not bind IL-13, it appears that the functional IL-4R and IL-13R share a common subunit that is important for signal transduction.

Answer A1: Interleukin 13 (IL-13) is a recently described protein secreted by activated T cells which is a potent in vitro modulator of human monocyte and B-cell functions. It is similar to IL-4.

Abstract A2: Interleukin-13 (IL-13), like IL-4, is a cytokine produced by TH2 type helper T cells in response to signaling through the T cell antigen receptor and by mast cells and basophils upon cross-linkage of the high-affinity receptor for immunoglobulin E (IgE). It is also produced by activated eosinophils. IL-13 induces many of the same responses as IL-4 and shares a receptor subunit with IL-4. IL-13 has been implicated in airway hypersensitivity and mucus hypersecretion, inflammatory bowel disease, and parasitic nematode expulsion.

Answer A2: Interleukin-13 (IL-13) is a cytokine produced by TH2 type helper T cells, mast cells, basophils, and eosinophils. It has been implicated in airway hypersensitivity and mucus hypersecretion, inflammatory bowel disease, and parasitic nematode expulsion. It is similar to IL-4.

Abstract A3: The recently cloned human interleukin 13 (IL-13) is a novel cytokine expressed in activated T cells that has been shown to inhibit inflammatory cytokine production by lipopolysaccharide-activated monocytes. The protein encoded by the IL-13 cDNA is the human homologue of a mouse Th2-product called P600. Here, we show that IL-13 acts at different stages of the B cell maturation pathway: (a) it enhances the expression of CD23/Fc epsilon RII and class II MHC antigens on resting B cells; (b) it stimulates B cell proliferation in combination with anti-Ig and anti-CD40 antibodies; and (c) it induces IgE synthesis. Thus, the spectrum of the biological activities of IL-13 on B cells largely overlaps that previously ascribed to IL-4. The present observations suggest that IL-13 may be an important factor, in addition to IL-4, in the development of allergic diseases.

Answer A3: Interleukin 13 (IL-13) is a novel cytokine expressed in activated T cells that has been shown to inhibit inflammatory cytokine production. It does similar things to IL-4 and may be an important factor in the development of allergic diseases.

Abstract A4: The discovery of new cytokines normally relies on a prior knowledge of at least one of their biological effects, which is used as a criterion either for the purification of the protein or for the isolation of the complementary DNA by expression cloning. However, the redundancy of cytokine activities complicates the discovery of novel cytokines in this way, and the pleiotropic nature of many cytokines means that the principal activities of a new cytokine may bear little relation to that used for its isolation. We have adopted an alternative approach which relies on differential screening of an organized subtracted cDNA library from activated peripheral blood mononuclear cells, using the inducibility of lymphokine messenger RNAs by anti-CD28 as a primary screening criterion. The ligation of the CD28 antigen on the T lymphocyte by a surface antigen, B7/BB-1, expressed on activated B lymphocytes and monocytes is a key step in the activation of T lymphocytes and the accumulation of lymphokine mRNAs. Here we report the discovery by molecular cloning of a new interleukin (interleukin-13 or IL-13) expressed in activated human T lymphocytes. Recombinant IL-13 protein inhibits inflammatory cytokine production induced by lipopolysaccharide in human peripheral blood monocytes. Moreover, it synergizes with IL-2 in regulating interferon-gamma synthesis in large granular lymphocytes. Recent mapping of the IL-13 gene shows that it is closely linked to the IL-4 gene on chromosome 5q 23-31 (ref. 4). Interleukin-13 may be critical in regulating inflammatory and immune responses.

Answer A4: Recombinant Interleukin-13 (IL-13) protein inhibits inflammatory cytokine production induced by lipopolysaccharide in human peripheral blood monocytes. Moreover, it synergizes with IL-2 in regulating interferon-gamma synthesis in large granular lymphocytes.

Combined Answer A with references to A1-A4: IL-13 is a cytokine protein secreted by T cells, mast cells, basophils, and eosinophils in humans (A1; A2; A3). It modulates monocyte and B-cell functions and inhibits imflmmatory cytokine production (A1; A3; A4) and is implicated in airway hypersensitivity and mucus hypersecretion, inflammatory bowel disease, and parasitic nematode expulsion (A2). It is similar to IL-4 (A1; A2; A3).

###

Question B: {question}

{abstract_answers_str}

Combined Answer B with references to B1-B4:"""


async def combine_abstract_answers(
    question: str, abstracts: list[Abstract], answers: list[str]
) -> str:
    prompt = make_prompt(question=question, abstracts=abstracts, answers=answers)
    answer = await recipe.agent().complete(prompt=prompt, stop="###")
    return answer


async def combine_abstract_answers_cli() -> str:
    abstracts = DEFAULT_ABSTRACTS
    question = "what is the relationship between income and smoking?"
    answers = [
        "Studies worldwide show a consistent inverse dose-response relationship between cigarette smoking and income level, present among most geographical areas and country characteristics.",
        "Income and education are both related to smoking in the EU",
        "There is an inverse relationship between income and smoking prevalence in studies from Latin America",
        "Education and income are both negatively related to smoking in health surveys in Hungary",
    ]
    return await combine_abstract_answers(
        question=question, abstracts=abstracts, answers=answers
    )


recipe.main(combine_abstract_answers_cli)
