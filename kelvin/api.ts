import { Action, Card, CardView, Workspace } from "/types";

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8935/kelvin";

export async function getWorkspace({ workspaceId }: { workspaceId: string }) {
  const response = await fetch(`${backendUrl}/workspaces/${workspaceId}`);
  const workspace = await response.json();
  return workspace;
}

export async function getInitialWorkspace() {
  const response = await fetch(`${backendUrl}/workspaces/initial`);
  const workspace = await response.json();
  return workspace;
}

export async function updateWorkspace({ workspace }: { workspace: Workspace }) {
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

export async function executeAction({
  card,
  view,
  action,
}: {
  card: Card;
  view: CardView;
  action: Action;
}) {
  const requestBody = JSON.stringify({ card, view, action });
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

export async function getAvailableActions({ card, view }: { card: Card; view: CardView }) {
  console.log("getAvailableActions", { card, view });
  const requestBody = JSON.stringify({ card, view });
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
