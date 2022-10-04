import Head from "next/head";
import Link from "next/link";
import { recipes } from "/helpers/recipes";

export default function HomePage() {
  return (
    <div className="m-8">
      <Head>
        <title>Interactive Composition Explorer</title>
      </Head>
      <h1 className="text-xl font-bold mb-2">Recipes</h1>
      <ul className="grid grid-cols-1 list-none">
        {Object.entries(recipes).map(([traceId, { title, description, hidden }]) => {
          if (hidden) return null;
          return (
            <li key={traceId} className="p-2">
              <Link href={`/traces/${traceId}`}>
                <a className="flex items-center">
                  <div className="flex-1">
                    <h2 className="text-l font-semibold">{title}</h2>
                    <p className="text-gray-600">{description}</p>
                  </div>
                </a>
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
