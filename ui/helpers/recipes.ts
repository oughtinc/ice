export interface Recipe {
  title: string;
  description?: string;
  hidden?: boolean;
}

export type Recipes = Record<string, Recipe>;

export const elicitRecipes: Recipes = {
  "01GCZNZ1YC0XRE1QHSAV6MPWJD": {
    title: "Placebo classification and description",
    description: "Did this paper use a placebo? If so, what was it?",
  },
  "01GBXP1B256Z9VRGPWC2JYT14H": {
    title: "Adherence via multilevel classification and chain-of-thought sampling",
    description: "What was the adherence/drop-out rate of the experiment?",
  },
  "01GBXKV6EK63YW503VTMMSER3B": {
    title: "Experiments and arms baseline using simple comparisons question-answering",
    description:
      "What separate experiments were conducted, and for each experiment, what were the trial arms? Baseline approach using simple decomposition.",
  },
  "01GFRJDVHF2BG21SP22VB8M6N1": {
    title: "Experiments and arms using chain-of-thought to rank and answer",
    description:
      "What separate experiments were conducted, and for each experiment, what were the trial arms? Decompose into separate questions, rank passages, and use chain-of-thought reasoning to answer.",
  },
  "01GBXTYND8V67HH5H1GWZWJKGB": {
    title: "Evaluation of results",
    description:
      "Find differences between gold standard and model results, classify as good or not",
  },
  "01GCB3AT0P2GQBBYXNBVP8VT1E": {
    title: "Placebo description + evaluation",
    description:
      "Describe Placebo (assuming there is one), then auto-evaluate against gold standards",
  },
  "01GFRBF0HXC1VMGK210QFWPNC0": {
    title: "Sample size per trial arm at randomization",
    description: "For each experiment and trial arm, what was the sample size at randomization?",
  },
  "01GFRNYGHZ98M50S4HVSBN5BNM": {
    title: "Search and synthesize",
    description:
      "Run a search using the Elicit API and generate a synthesis of the returned abstracts",
  },
};

export const primerRecipes: Recipes = {
  "01GE0GN5PPQWYGMT1B4GFPDZ09": {
    title: "Hello world",
    hidden: true,
  },
  "01GE0H8AM335QSV25E3ZYZ1PGM": {
    title: "qa_simple",
    hidden: true,
  },
  "01GE0V4J1PR5SXMW0TRMW9GX1Z": {
    title: "Q&A",
    description: "A simple trace that makes a single language model call",
  },
  "01GE0VA96FWT7SSQNXD6CQH4BT": {
    title: "Debate",
    description: "Language models debating a claim",
  },
  "01GE0VFJXGJZYGN9YDF8TN6D9E": {
    title: "paper_hello",
    hidden: true,
  },
  "01GE0VH9CKF25WJ7V65HAW8PKD": {
    title: "paper_qa_class",
    hidden: true,
  },
  "01GE0VN9ASN2CTNCRQG0JPMQX8": {
    title: "paper_qa_classes",
    hidden: true,
  },
  "01GE0VP66QPHGXNWQ31HDB16E6": {
    title: "paper_qa_ranker",
    hidden: true,
  },
  "01GE0VT6FEBNVE84HCMCYZ2GX9": {
    title: "Paper Q&A",
    description:
      "Answer questions about a paper by classifying paragraph relevance, then answering given most relevant paragraphs",
  },
  "01GE0VXVNP2G2CDE7JKJ1GP8CC": {
    title: "subquestions",
    hidden: true,
  },
  "01GE0W06G8B3DP2EC8XEAR1WBF": {
    title: "subquestions_answered",
    hidden: true,
  },
  "01GE0W2SK5VP21VTBF5PEHGR8R": {
    title: "amplify_one",
    hidden: true,
  },
  "01GE0W6DHC42P1931W6P2PZQ34": {
    title: "Amplification",
    description: "Answer a question by (recursive) amplification: Ask & answer subquestions",
  },
  "01GE0WDKKARCGQR9PHH4799H95": {
    title: "verify_answer",
    hidden: true,
  },
  "01GE0WG325B7V00XKVYV7JGXC5": {
    title: "verify/last",
    hidden: true,
  },
  "01GE0WHGQ89V3QC0DHNAE06JPQ": {
    title: "Verify reasoning steps",
    description: "Check reasoning steps for a math problem",
  },
  "01GE0WVSS2622HPERJ6FC7MQXY": {
    title: "answer_by_search_direct",
    hidden: true,
  },
  "01GE0WYTARJR6PK7QY5RJDGZPR": {
    title: "Answer by search",
    description:
      "Answer a question by generating a web search query, then answering given the results",
  },
  "01GE0XAYWSKX59VXRP0QQBFTQV": {
    title: "eval_selective",
    hidden: true,
  },
  "01GE0XFAVDNWSP5TNWZ944NWSW": {
    title: "Answer by computation",
    description:
      "Answer a question by generating a Python expression to evaluate, then answering given the result",
  },
  "01GE0XHSF1RDJKCPTZ4ZWW5297": {
    title: "chain_of_thought",
    hidden: true,
  },
  "01GE0XKTG8VWYBTXXGFF1GPFBC": {
    title: "Answer by reasoning",
    description: "Answer a question by writing out a chain of thought.",
  },
  "01GE0XSKXKVVK6KB56AN6VGZ6C": {
    title: "answer_by_dispatch/classification",
    hidden: true,
  },
  "01GE0XVZW2TA6X0WC205WY5N42": {
    title: "One-shot action selection",
    description:
      "Answer by choosing which action to execute: web search, computation, or reasoning steps",
  },
  "01GE0XYTCPNZN5MKQ23TNJV53B": {
    title: "Iterative action selection",
    description:
      "Choose a sequence of actions, one by one. At each step, ask if you have enough info to answer.",
  },
};

export const recipes = {
  ...elicitRecipes,
  ...primerRecipes,
};
