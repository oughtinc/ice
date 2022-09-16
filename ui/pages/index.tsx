import Link from "next/link";

const recipes = [
  {
    link: "/traces/01GCZNZ1YC0XRE1QHSAV6MPWJD",
    title: "Placebo classification and description",
    description: "Did this paper use a placebo? If so, what was it?",
  },
  {
    link: "/traces/01GBXP1B256Z9VRGPWC2JYT14H",
    title: "Adherence via multilevel classification and chain-of-thought sampling",
    description: "What was the adherence/drop-out rate of the experiment?",
  },
  {
    link: "/traces/01GBXKV6EK63YW503VTMMSER3B",
    title: "Experiments and Arms baseline using simple comparisons question-answering",
    description:
      "What separate experiments were conducted, and for each experiment, what were the trial arms?",
  },
  {
    link: "/traces/01GBXTYND8V67HH5H1GWZWJKGB",
    title: "Evaluation of results",
    description:
      "Find differences between gold standard and model results, classify as good or not",
  },
  {
    link: "/traces/01GCB3AT0P2GQBBYXNBVP8VT1E",
    title: "Placebo description + evaluation",
    description:
      "Describe Placebo (assuming there is one), then auto-evaluate against gold standards",
  },
  // Add more recipes here
];

export default function HomePage() {
  return (
    <div className="m-8">
      <h1 className="text-xl font-bold mb-2">Recipes</h1>
      <ul className="grid grid-cols-1 list-none">
        {recipes.map(recipe => (
          <li key={recipe.link} className="p-2">
            <Link href={recipe.link}>
              <a className="flex items-center">
                <div className="flex-1">
                  <h2 className="text-l font-semibold">{recipe.title}</h2>
                  <p className="text-gray-600">{recipe.description}</p>
                </div>
              </a>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
