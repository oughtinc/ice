import { Link } from "react-router-dom";
import type { Recipe } from "/helpers/recipes";
import { elicitRecipes, primerRecipes } from "/helpers/recipes";
import React, { useEffect } from "react";

interface RecipeGroupProps {
  title: string;
  recipes: Record<string, Recipe>; // assuming traceId is a string
  children?: React.ReactNode;
}

function RecipeGroup({ title, recipes, children }: RecipeGroupProps) {
  return (
    <>
      <h2 className="text-lg font-semibold mt-8">{title}</h2>
      <div className="p-2 pl-0">{children}</div>
      <ul className="grid grid-cols-1 list-none">
        {Object.entries(recipes).map(([traceId, { title, description, hidden }]) => {
          if (hidden) return null;
          return (
            <li key={traceId} className="p-2 pl-0">
              <Link to={`/traces/${traceId}`}>
                <a className="flex items-center">
                  <div className="flex-1">
                    <h3 className="text-l font-semibold">{title}</h3>
                    <p className="text-gray-600">{description}</p>
                  </div>
                </a>
              </Link>
            </li>
          );
        })}
      </ul>
    </>
  );
}

export default function HomePage() {
  useEffect(() => {
    document.title = "Interactive Composition Explorer (ICE)";
  }, []);
  return (
    <div className="m-12">
      <h1 className="text-xl font-bold mb-2">Interactive Composition Explorer (ICE)</h1>
      <p>
        <a href="https://github.com/oughtinc/ice">ICE</a> is an open-source Python library and trace
        visualizer for compositional language model programs. This page hosts a collection of traces
        that demonstrate programs written in ICE.
      </p>
      <RecipeGroup title="Elicit" recipes={elicitRecipes}>
        <p>
          <a href="https://elicit.org/">Elicit</a> is an AI research assistant. The traces below
          show some of the programs we&apos;ve been working on as part of Elicit.
        </p>
      </RecipeGroup>
      <RecipeGroup title="Primer" recipes={primerRecipes}>
        <p>
          The <a href="https://primer.ought.org/">Factored Cognition Primer</a> is a tutorial that
          demonstrates how to use ICE to build simple compositional language model programs. The
          traces below are some of the programs covered by the tutorial.
        </p>
      </RecipeGroup>
    </div>
  );
}
