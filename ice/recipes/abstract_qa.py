from dataclasses import dataclass
from typing import Optional

from ice.recipe import recipe


@dataclass
class Abstract:
    title: str
    authors: list[str]
    year: Optional[int]
    text: str


DEFAULT_ABSTRACTS = [
    Abstract(
        title="Association Between Cigarette Smoking Prevalence and Income Level: A Systematic Review and Meta-Analysis",
        authors=[
            "Brunilda Casetta",
            "Alejandro J Videla",
            "Ariel Bardach",
            "Paola Morello",
            "Natalie Soto",
            "Kelly Lee",
            "Paul Anthony Camacho",
            "Rocío Victoria Hermoza Moquillaza",
            "Agustín Ciapponi",
        ],
        year=2016,
        text="""Introduction Previous evidence linked low socioeconomic status with higher smoking prevalence. Our objective was to assess the strength of this association in the world population, updating a previous work.
Methods Systematic review and meta-analysis of observational studies. Subgroup analyses included continents, WHO regions, country mortality levels, gender, age, risk of bias, and study publication date. Independent reviewers selected studies, assessed potential bias and extracted data. We searched MEDLINE, EMBASE, CENTRAL, SOCINDEX, AFRICAN INDEX MEDICUS, and LILACS, and other sources from 1989 to 2013 reporting direct measurements of income and current cigarette smoking.
Results We retrieved 13,583 articles and included 93 for meta-analysis. Median smoking prevalence was 17.8% (range 3-70%). Lower income was consistently associated with higher smoking prevalence (odds ratio [OR]: 1.45; 95% confidence interval [CI]: 1.35-1.56). This association was statistically significant in the subgroup analysis by WHO regions for the Americas (OR: 1.54; 95% CI: 1.42-1.68), South East Asia (OR: 1.53; 95% CI: 1.10-2.00), Europe (OR: 1.45; 95% CI: 1.29-1.63), and Western Pacific (OR: 1.32; 95% CI: 1.02-1.72), and in studies conducted during 1990s (OR: 1.42; 95% CI: 1.24-1.62) and 2000s (OR: 1.48; 95%CI: 1.30-1.64). Likewise, it was noted in low-mortality countries (OR: 1.48; 95% CI: 1.37-1.60) and for both genders. Prevalence was highest in the lowest income levels compared to the middle (OR: 1.69; 95% CI: 1.49-1.92), followed by the middle level compared to the highest (OR: 1.31; 95% CI: 1.20-1.43).
Conclusions Our results show that current cigarette smoking was significantly associated with lower income worldwide and across subgroups, suggesting a dose-response relationship.
Implications This unique updated systematic review shows a consistent inverse dose-response relationship between cigarette smoking and income level, present among most geographical areas and country characteristics. Public health measures should take into account this potential inequity and consider special efforts directed to disadvantaged populations.""",
    ),
    Abstract(
        title="Educational inequalities in cause-specific mortality in middle-aged and older men and women in eight western European populations",
        authors=[
            "Martijn Huisman",
            "Anton E Kunst",
            "Matthias Bopp",
            "Jens-Kristian Borgan",
            "Carme Borrell",
            "Giuseppe Costa",
            "Patrick Deboosere",
            "Sylvie Gadeyne",
            "Myer Glickman",
            "Chiara Marinacci",
            "Christoph Minder",
            "Enrique Regidor",
            "Tapani Valkonen",
            "Johan P Mackenbach",
        ],
        year=2005,
        text="""BACKGROUND The aim of the study was to determine whether education or income was more strongly related to smoking in the European Union at large, and within the individual countries of the EU, at the end of the 1990s.
METHODS We related smoking prevalence to education and income level by analyzing cross-sectional data on a total of 48,694 men and 52,618 women aged 16 and over from 11 countries of the European Union in 1998.
RESULTS Both education and income were related to smoking within the European Union at large. After adjustment of the other socioeconomic indicator, education remained related to smoking in the EU at large, but income only remained so among men. Educational inequalities were larger than income-related inequalities among younger and middle-aged men and women. Educational inequalities were larger than income-related inequalities among men in all individual countries, and among women in Northern Europe. For women from Southern European countries, the magnitude of education- and income-related inequalities was similar.
CONCLUSIONS Education is a strong predictor of smoking in Europe. Interventions should aim to prevent addiction to smoking among the lower educated, by price policies, school-based programs, and smoking cessation support for young adults.""",
    ),
    Abstract(
        title="Income levels and prevalence of smoking in Latin America",
        authors=[
            "Ariel Bardach",
            "Herney Andrés García Perdomo",
            "Ruth Amanda Ruano Gándara",
            "Agustín Ciapponi",
        ],
        year=2016,
        text="""Objective Determine the relationship between tobacco-use prevalence and smoker income level in Latin America and the Caribbean (LAC).
Methods A systematic search was carried out in MEDLINE, EMBASE, CENTRAL, SOCINDEX, and LILACS databases. Studies from LAC published from January 1989 to December 2015 were included and were analyzed by subgroups disaggregated by decade of data, country, bias risk, sex, and age group.
Results Of 1 254 studies evaluated by full text, 29 articles were included, of which 25 were chosen for meta-analysis. All included studies were cross-sectional or surveillance, primarily from Brazil and Mexico.Low income was associated with higher prevalence of active smoking (odds ratio [OR] 1.62; 95% confidence interval [95%CI] 1.34-1.96) than high income (reference). A dose-response effect trend was observed: middle income (OR 1.23; 95%CI 1.00-1.52) and low income (OR 1.64; 95%CI 1.17-2.30). This association was greater in men (OR 2.22; 95%CI 1.77-2.78) than in women (OR 1.6; 95%CI 1.11-2.47).
Conclusions An inverse relationship was observed between income and tobacco-use prevalence. Further efforts are required to determine this relationship in special populations, such as adolescents and pregnant women. This research can be useful for policymakers by improving tobacco control strategies and for characterizing public health equity issues.""",
    ),
    Abstract(
        title="Is income or employment a stronger predictor of smoking than education in economically less developed countries? A cross-sectional study in Hungary",
        authors=["Mall Leinsalu", "Csilla Kaposvári", "Anton E Kunst"],
        year=2011,
        text="""BackgroundIn developed European countries in the last phase of the smoking epidemic, education is a stronger predictor of smoking than income or employment. We examine whether this also applies in economically less developed countries.MethodsData from 7218 respondents in the 25-64 age group came from two National Health Interview Surveys conducted in 2000 and 2003 in Hungary. Independent effects of educational level, income and employment status were studied in relation to smoking prevalence, initiation and continuation for all age groups combined and separately for 25-34, 35-49 and 50-64 years old. Absolute levels were evaluated by using age-standardized prevalence rates. Relative differences were assessed by means of logistic regression.ResultsEducation and income, but not employment, were associated with equally large differences in smoking prevalence in Hungary in the 25-64 age group. Among men, smoking initiation was related to low educational level, whereas smoking continuation was related to low income. Among women, low education and low income were associated with both high initiation and high continuation rates. Considerable differences were found between the age groups. Inverse social gradients were generally strongest in the youngest age groups. However, smoking continuation among men had the strongest association with low income for the middle-aged group.ConclusionsPatterns of inequalities in smoking in Hungary can be best understood in relation to two processes: the smoking epidemic, and the additional effects of poverty. Equity orientated tobacco control measures should target the low educated to prevent their smoking initiation, and the poor to improve their cessation rates.""",
    ),
]


def make_prompt(abstract: Abstract, question: str) -> str:
    return f"""Answer the given question about each abstract:

###

Question 1: What is IL-13?

Title 1: Interleukin 13, an interleukin 4-like cytokine that acts on monocytes and B cells, but not on T cells

Abstract 1: Interleukin 13 (IL-13) is a recently described protein secreted by activated T cells which is a potent in vitro modulator of human monocyte and B-cell functions. The data, reviewed here by Gerard Zurawski and Jan de Vries, shows that IL-13 shares biological activities with IL-4, their genes are closely linked in both the human and mouse genomes, and there is sequence homology between IL-13 and IL-4 proteins. Although the cloned IL-4 receptor protein (IL-4R) does not bind IL-13, it appears that the functional IL-4R and IL-13R share a common subunit that is important for signal transduction.

Answer 1: Interleukin 13 (IL-13) is a recently described protein secreted by activated T cells which is a potent in vitro modulator of human monocyte and B-cell functions. It is similar to IL-4.

###

Question 2: What are the challenges in multi-agent systems?

Title 2: Multi-Agent Systems: Technical & Ethical Challenges of Functioning in a Mixed Group

Abstract 2: In today's highly interconnected, open-networked computing world, artificial intelligence computer agents increasingly interact in groups with each other and with people both virtually and in the physical world. AI's current core challenges concern determining ways to build AI systems that function effectively and safely for people and the societies in which they live. To incorporate reasoning about people, research in multi-agent systems has engendered paradigmatic shifts in computer-agent design, models, and methods, as well as the development of new representations of information about agents and their environments. These changes have raised technical as well as ethical and societal challenges. This essay describes technical advances in computer-agent representations, decision-making, reasoning, and learning methods and highlights some paramount ethical challenges.

Answer 2: The paper is not directly relevant to the question. The paper argues that research in multi-agent systems has raised societal and ethical challenges.

###

Question 3: {question}

Title 3: {abstract.title}

Abstract 3: {abstract.text}

Answer 3:"""


async def abstract_qa(
    abstract: Abstract,
    question: str,
) -> str:
    prompt = make_prompt(abstract=abstract, question=question)
    answer = await recipe.agent().complete(prompt=prompt, stop="###")
    return answer


async def abstract_qa_cli():
    abstract = DEFAULT_ABSTRACTS[0]
    question = "what is the relationship between income and smoking?"
    answer = await abstract_qa(abstract=abstract, question=question)
    return answer


recipe.main(abstract_qa_cli)
