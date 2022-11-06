import { Workspace } from "../types";

export function getCurrentCard(workspace: Workspace | null) {
  if (!workspace) return null;
  const { cards, view } = workspace;
  if (!view || !cards) return null;
  return cards.find(card => card.id === view.card_id);
}

export function getCurrentActions(workspace: Workspace | null) {
  if (!workspace) return null;
  return workspace.available_actions;
}

export function getSelectedCardRows(workspace: Workspace | null) {
  if (!workspace) return null;
  const { view } = workspace;
  if (!view) return null;
  return view.selected_rows;
}

export function getCurrentCardWithView(workspace: Workspace | null) {
  if (!workspace) return null;
  const { cards, view } = workspace;
  const currentCard = getCurrentCard(workspace);
  if (!currentCard) return null;
  return { card: currentCard, view };
}

export function getFocusIndex(workspace: Workspace | null) {
  if (!workspace) return null;
  const { view } = workspace;
  if (!view) return null;
  return view.focused_row_index;
}
