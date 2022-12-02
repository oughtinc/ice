import { History, Workspace } from "../types";

export function getAvailableActions(workspace: Workspace | null) {
  if (!workspace) return null;
  return workspace.available_actions;
}

export function getCurrentCard(workspace: Workspace | null): Card | null {
  if (workspace === null || workspace.paths == null) {
    return null;
  }
  const focusPath = workspace.paths[workspace.focus_path_id];
  if (focusPath === null) {
    return null;
  }
  const headCard = workspace.cards[focusPath.head_card_id];
  return headCard;
}

export function getSelectedCardRows(workspace: Workspace | null): Row[] {
  const card = getCurrentCard(workspace);
  if (card === null) {
    return [];
  }
  const view = workspace.paths[workspace.focus_path_id].view;
  const selectedRows = card.rows.filter(row => view.selected_row_ids[row.id]);
  return selectedRows;
}

export function getFocusPath(workspace: Workspace | null): Path | null {
  if (workspace === null || workspace.paths == null) {
    return null;
  }
  const focusPath = workspace.paths[workspace.focus_path_id];
  return focusPath;
}

export function getFrontier(workspace: Workspace | null): Frontier | null {
  if (workspace === null) {
    return null;
  }
  const frontier: Frontier = {
    paths: {},
    focus_path_id: workspace.focus_path_id,
  };
  for (const pathId of Object.keys(workspace.paths)) {
    const path = workspace.paths[pathId];
    const card = workspace.cards[path.head_card_id];
    const hydratedPath: HydratedPath = {
      id: path.id,
      label: path.label,
      head_card: card,
      view: path.view,
    };
    frontier.paths[pathId] = hydratedPath;
  }
  return frontier;
}

export function getFocusIndex(workspace: Workspace | null): number | null {
  if (workspace === null || workspace.paths == null) {
    return null;
  }
  const focusPath = workspace.paths[workspace.focus_path_id];
  return focusPath?.view?.focused_row_index;
}

export function updateWorkspace(workspace: Workspace, partialFrontier: PartialFrontier): Workspace {
  const updatedWorkspace: Workspace = { ...workspace };

  // Iterate over the paths in the partial frontier
  for (const [pathId, hydratedPath] of Object.entries(partialFrontier.paths)) {
    if (workspace.paths[pathId]) {
      // If the path already exists, update it

      const isNewCard = hydratedPath.head_card.id != workspace.paths[pathId].head_card_id;
      // Update the path in the workspace with the new head card, view and label
      updatedWorkspace.paths[pathId] = {
        id: pathId,
        label: hydratedPath.label,
        head_card_id: hydratedPath.head_card.id,
        view: hydratedPath.view,
      };
      if (isNewCard) {
        // Update the cards in workspace with new head cards
        updatedWorkspace.cards[hydratedPath.head_card.id] = hydratedPath.head_card;
        // For the card that has been replaced, make next_id point to the new head card
        updatedWorkspace.cards[hydratedPath.head_card.prev_id].next_id = hydratedPath.head_card.id;
      }
    } else {
      // create a new path
      updatedWorkspace.paths[pathId] = {
        id: pathId,
        label: hydratedPath.label,
        head_card_id: hydratedPath.head_card.id,
        view: hydratedPath.view,
      };
      // add the head card to the workspace
      updatedWorkspace.cards[hydratedPath.head_card.id] = hydratedPath.head_card;
    }
  }

  // Update the focus path id if it is different in the partial frontier
  updatedWorkspace.focus_path_id = partialFrontier.focus_path_id;

  // Return the updated workspace
  return updatedWorkspace;
}

// A helper function that counts the number of cards in a linked list starting from a given card
function countSuccessorCards({
  card,
  cards,
}: {
  card: Card | null;
  cards: Record<CardId, Card>;
}): number {
  let count = 0;
  let current = card;
  while (current) {
    count++;
    current = current.next_id ? cards[current.next_id] : null;
  }
  return count;
}

// A function that takes a card and computes its position in the sequence
export function cardPosition({ card, cards }: { card: Card; cards: Record<CardId, Card> }): {
  total: number;
  index: number;
} {
  const successors = countSuccessorCards({ card, cards });

  // Count the number of cards before the current card
  let predecessors = 0;
  let current = card.prev_id ? cards[card.prev_id] : null;
  while (current) {
    predecessors++;
    current = current.prev_id ? cards[current.prev_id] : null;
  }

  const total = predecessors + successors;

  // Return the total and the index
  return { total, index: predecessors };
}

export function getHistory(workspace: Workspace | null): History | null {
  // If the workspace is null, return null
  if (workspace === null) {
    return null;
  }

  // Get the focus path
  const focusPath = getFocusPath(workspace);
  if (focusPath === null) {
    return null;
  }

  // Get the head card
  const headCard = workspace.cards[focusPath.head_card_id];
  if (headCard === null) {
    return null;
  }

  // Initialize the history array
  const history: History = [];

  // Start with the head card and iterate backwards through the linked list
  let current = headCard;
  while (current) {
    // Add the card to the history array
    history.unshift({ card: current, action: current.created_by_action });

    // Get the previous card
    current = current.prev_id ? workspace.cards[current.prev_id] : null;
  }

  // Return the history
  return history;
}
