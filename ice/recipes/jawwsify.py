from ice.apis.openai import openai_complete
from ice.recipe import recipe

# TODO: Citation removal isn't what we want we should instead:
# a) Extract them into a "footnotes" section, and keep the footnote links inline
# b) Remove them from the text, and then add them back in at the very end
# Would also need us to test how well the agent keeps the footnote links in the right place

CITATION_REMOVAL_PROMPT = """Rewrite the following paragraphs to make them more readable, according to the following rule:
- Remove all inline citations, but otherwise leave the text unchanged."""

SPLIT_PROMPT = """Rewrite the following paragraphs to make them more readable, according to the following rule:
- Break up the single large paragraph into multiple paragraphs, along natural paragraph boundaries."""

SIMPLIFY_PROMPT = """Rewrite the following paragraphs to make them more readable, according to the following rule:
- Make explanations more generally accessible, by providing longer explanations for any particularly complicated concepts.
- Make the writing generally clearer, simpler, and make it flow more smoothly. """

EXAMPLE_0 = """Most models of trait evolution are based on the Brownian motion model (Cavalli-Sforza & Edwards 1967; Felsenstein 1973). The Ornstein–Uhlenbeck (OU) model can be thought of as a modification of the Brownian model with an additional parameter that measures the strength of return towards a theoretical optimum shared across a clade or subset of species (Hansen 1997; Butler & King 2004). OU models have become increasingly popular as they tend to fit the data better than Brownian motion models, and have attractive biological interpretations (Cooper et al. 2016b). For example, fit to an OU model has been seen as evidence of evolutionary constraints, stabilising selection, niche conservatism and selective regimes (Wiens et al. 2010; Beaulieu et al. 2012; Christin et al. 2013; Mahler et al. 2013). However, the OU model has several well-known caveats (see Ives & Garland 2010; Boettiger, Coop & Ralph 2012; Hansen & Bartoszek 2012; Ho & Ané 2013, 2014). For example, it is frequently incorrectly favoured over simpler models when using likelihood ratio tests, particularly for small data sets that are commonly used in these analyses (the median number of taxa used for OU studies is 58; Cooper et al. 2016b). Additionally, very small amounts of error in data sets can result in an OU model being favoured over Brownian motion simply because OU can accommodate more variance towards the tips of the phylogeny, rather than due to any interesting biological process (Boettiger, Coop & Ralph 2012; Pennell et al. 2015). Finally, the literature describing the OU model is clear that a simple explanation of clade-wide stabilising selection is unlikely to account for data fitting an OU model (e.g. Hansen 1997; Hansen & Orzack 2005), but users of the model often state that this is the case. Unfortunately, these limitations are rarely taken into account in empirical studies."""
EXAMPLE_1 = """Most models of trait evolution are based on the Brownian motion model. The Ornstein–Uhlenbeck (OU) model can be thought of as a modification of the Brownian model with an additional parameter that measures the strength of return towards a theoretical optimum shared across a clade or subset of species. OU models have become increasingly popular as they tend to fit the data better than Brownian motion models, and have attractive biological interpretations. For example, fit to an OU model has been seen as evidence of evolutionary constraints, stabilising selection, niche conservatism and selective regimes. However, the OU model has several well-known caveats. For example, it is frequently incorrectly favoured over simpler models when using likelihood ratio tests, particularly for small data sets that are commonly used in these analyses. Additionally, very small amounts of error in data sets can result in an OU model being favoured over Brownian motion simply because OU can accommodate more variance towards the tips of the phylogeny, rather than due to any interesting biological process. Finally, the literature describing the OU model is clear that a simple explanation of clade-wide stabilising selection is unlikely to account for data fitting an OU model, but users of the model often state that this is the case. Unfortunately, these limitations are rarely taken into account in empirical studies."""
EXAMPLE_2 = """Most models of trait evolution are based on the Brownian motion model.

The Ornstein–Uhlenbeck (OU) model can be thought of as a modification of the Brownian model with an additional parameter that measures the strength of return towards a theoretical optimum shared across a clade or subset of species. OU models have become increasingly popular as they tend to fit the data better than Brownian motion models, and have attractive biological interpretations. For example, fit to an OU model has been seen as evidence of evolutionary constraints, stabilising selection, niche conservatism and selective regimes.

However, the OU model has several well-known caveats. For example, it is frequently incorrectly favoured over simpler models when using likelihood ratio tests, particularly for small data sets that are commonly used in these analyses. Additionally, very small amounts of error in data sets can result in an OU model being favoured over Brownian motion simply because OU can accommodate more variance towards the tips of the phylogeny, rather than due to any interesting biological process. Finally, the literature describing the OU model is clear that a simple explanation of clade-wide stabilising selection is unlikely to account for data fitting an OU model, but users of the model often state that this is the case. Unfortunately, these limitations are rarely taken into account in empirical studies."""
EXAMPLE_3 = """Most models of trait evolution are based on the Brownian motion model, in which traits evolve randomly and accrue variance over time.

What if we add a parameter to measure how much the trait motion returns to a theoretical optimum for a given clade or set of species? Then we get a family of models called Ornstein-Uhlenbeck, first developed as a way to describe friction in the Brownian motion of a particle. These models have become increasingly popular, both because they tend to fit the data better than simple Brownian motion, and because they have attractive biological interpretations. For example, fit to an Ornstein-Uhlenbeck model has been seen as evidence of evolutionary constraints, stabilising selection, niche conservatism and selective regimes.

However, Ornstein-Uhlenbeck models have several well-known caveats. For example, they are frequently — and incorrectly — favoured over simpler Brownian models. This occurs with likelihood ratio tests, particularly for the small data sets that are commonly used in these analyses. It also happens when there is error in the data set, even very small amounts of error, simply because Ornstein-Uhlenbeck models accommodate more variance towards the tips of the phylogeny — therefore suggesting an interesting biological process where there is none. Additionally, users of Ornstein-Uhlenbeck models often state that clade-wide stabilising selection accounts for data fitting the model, even though the literature describing the model warns that such a simple explanation is unlikely. Unfortunately, these limitations are rarely taken into account in empirical studies.
"""
SEP = "\n ### \n"

INITIAL_TEXT = """The majority of licensed vaccines provide protection through induction of protective antibodies (Plotkin, 2010). Isolation of HIV-1 broadly neutralizing antibodies (bnAbs) from HIV-infected individuals and the finding that passive transfer of bnAbs can protect non-human primates (NHPs) from simian/human immunodeficiency virus (SHIV) infection support the feasibility of an antibody-based HIV vaccine (Burton and Hangartner, 2016, Nishimura and Martin, 2017). Elicitation of neutralizing antibodies (nAbs) against clinically relevant HIV strains (i.e., tier 2 and tier 3 strains) by immunization has been difficult (Montefiori et al., 2018). Much of that challenge centers on structural features of the HIV envelope (Env), which have complex and incompletely understood immunological implications. Env consists of gp120 and gp41 components that form a trimeric spike that is the only viral protein on HIV virions and the only target for nAbs (Burton and Hangartner, 2016). Human immunization with monomeric gp120 has failed to elicit tier 2 nAbs in clinical trials (Haynes et al., 2012, Mascola et al., 1996, Rerks-Ngarm et al., 2009). The reasons for this are not obvious because nAb epitopes are present on gp120. Key developments in protein design have been made toward the expression of soluble native-like HIV Env trimers (Julien et al., 2013, Kulp et al., 2017, Lyumkis et al., 2013, Sanders et al., 2013). Immunization with these Env trimers elicited substantial strain-specific tier 2 nAbs in rabbits and guinea pigs but failed to elicit nAbs in mice (Feng et al., 2016, Hu et al., 2015, Sanders et al., 2015). Trimer immunization of NHPs has been sporadically successful (Havenar-Daughton et al., 2016a, Pauthner et al., 2017, Sanders et al., 2015, Zhou et al., 2017). For some regimes in NHPs, autologous tier 2 nAbs have been elicited within 10 weeks, which is comparable with the speed of nAb development in HIV-infected individuals (Pauthner et al., 2017, Richman et al., 2003, Wei et al., 2003). Thus, although nAb epitopes are presented on native-like trimers, the immunological parameters controlling the development of nAbs to Env remain to be elucidated. These parameters are also likely important for nAbs to other pathogens."""


async def remove_citations(text: str):
    prompt = CITATION_REMOVAL_PROMPT
    prompt += SEP
    prompt += "Original text: " + EXAMPLE_0
    prompt += "\n"
    prompt += "Rewritten text: " + EXAMPLE_1
    prompt += SEP
    prompt += "Original text: " + text
    prompt += "\n"
    prompt += "Rewritten text:"

    return await recipe.agent().complete(prompt=prompt, max_tokens=2000)


async def split_paragraphs(text: str):
    prompt = SPLIT_PROMPT
    prompt += SEP
    prompt += "Original text: " + EXAMPLE_1
    prompt += "\n"
    prompt += "Rewritten text: " + EXAMPLE_2
    prompt += SEP
    prompt += "Original text: " + text
    prompt += "\n"
    prompt += "Rewritten text:"

    return await recipe.agent().complete(prompt=prompt, max_tokens=2000)


async def simplify(text: str):
    prompt = SEP
    prompt += SIMPLIFY_PROMPT
    prompt += "Original text: " + EXAMPLE_2
    prompt += "\n"
    prompt += "Rewritten text: " + EXAMPLE_3
    prompt += SEP
    prompt += SIMPLIFY_PROMPT
    prompt += "Original text: " + text
    prompt += "\n"
    prompt += "Rewritten text:"

    return await recipe.agent().complete(
        prompt=prompt, max_tokens=2000, frequency_penalty=0.5, presence_penalty=0.5
    )


async def pipeline(text: str = INITIAL_TEXT):
    text = await remove_citations(text)
    text = await split_paragraphs(text)
    text = await simplify(text)
    return text


recipe.main(pipeline)
