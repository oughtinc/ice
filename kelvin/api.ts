import { Action, Card, Workspace } from "/types";

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8935/kelvin";

export async function getWorkspace(workspaceId: string) {
  const response = await fetch(`${backendUrl}/workspaces/${workspaceId}`);
  const workspace = await response.json();
  return workspace;
}

export async function getInitialWorkspace() {
  const response = await fetch(`${backendUrl}/workspaces/initial`);
  const workspace = await response.json();
  return workspace;
}

export async function updateWorkspace(workspace: Workspace) {
  const response = await fetch(`${backendUrl}/workspaces/${workspace.id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(workspace),
  });
  const updatedWorkspace = await response.json();
  return updatedWorkspace;
}

export async function executeAction(action: Action, card: Card) {
  const requestBody = JSON.stringify({ action, card });
  const response = await fetch(`${backendUrl}/actions/execute`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: requestBody,
  });
  const newCard = await response.json();
  return newCard;
}
