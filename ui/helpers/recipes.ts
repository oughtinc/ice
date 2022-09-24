export const recipes: Record<string, { title: string; description: string }> = {
  "01GCZNZ1YC0XRE1QHSAV6MPWJD": {
    title: "Placebo classification and description",
    description: "Did this paper use a placebo? If so, what was it?",
  },
  "01GBXP1B256Z9VRGPWC2JYT14H": {
    title: "Adherence via multilevel classification and chain-of-thought sampling",
    description: "What was the adherence/drop-out rate of the experiment?",
  },
  "01GBXKV6EK63YW503VTMMSER3B": {
    title: "Experiments and Arms baseline using simple comparisons question-answering",
    description:
      "What separate experiments were conducted, and for each experiment, what were the trial arms?",
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
  // Add more recipes here
};
