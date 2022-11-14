import { Action, Frontier } from "/types";

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8935/kelvin";

export async function getInitialWorkspace() {
  const response = await fetch(`${backendUrl}/workspaces/initial`);
  const workspace = await response.json();
  return workspace;
}

export async function executeAction({ action, frontier }: { action: Action; frontier: Frontier }) {
  const requestBody = JSON.stringify({ action, frontier });
  const response = await fetch(`${backendUrl}/actions/execute`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: requestBody,
  });
  const newFrontier = await response.json();
  return newFrontier;
}

export async function getAvailableActions({ frontier }: { frontier: Frontier }) {
  const requestBody = JSON.stringify(frontier);
  const response = await fetch(`${backendUrl}/actions/available`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: requestBody,
  });
  const actions = await response.json();
  return actions;
}
