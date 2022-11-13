import React, { createContext, useContext, useEffect, useRef } from "react";
import { useImmerReducer } from "use-immer";
import {
  executeAction as apiExecuteAction,
  getAvailableActions,
  getInitialWorkspace,
  updateWorkspace,
} from "../api";
import { Workspace } from "../types";
import { getCurrentCard, getCurrentCardWithView } from "/utils/workspace";

type State = {
  workspace: Workspace | null;
  error: Error | null;
  activeRequestCount: number;
};

type ReducerAction =
  | { type: "FETCH_REQUEST" }
  | { type: "FETCH_FAILURE"; payload: Error }
  | { type: "FETCH_WORKSPACE_SUCCESS"; payload: Workspace }
  | { type: "UPDATE_WORKSPACE_SUCCESS"; payload: Workspace }
  | { type: "EXECUTE_ACTION_SUCCESS"; payload: Workspace }
  | {
      type: "SET_FOCUSED_ROW_INDEX";
      payload: number;
    }
  | {
      type: "SET_SELECTED_CARD_ROWS";
      payload: (rows: Record<string, boolean>) => Record<string, boolean>;
    }
  | { type: "UPDATE_AVAILABLE_ACTIONS_SUCCESS"; payload: Action[] }
  | { type: "SET_CARDVIEW_CARD_ID"; payload: string };

const initialState: State = {
  workspace: null,
  error: null,
  activeRequestCount: 0,
};

const reducer = (draft: State, action: ReducerAction) => {
  switch (action.type) {
    case "FETCH_REQUEST":
      draft.activeRequestCount++;
      draft.error = null;
      break;
    case "FETCH_FAILURE":
      draft.activeRequestCount--;
      draft.error = action.payload;
      break;
    case "FETCH_WORKSPACE_SUCCESS":
      draft.activeRequestCount--;
      draft.workspace = action.payload;
      break;
    case "UPDATE_WORKSPACE_SUCCESS":
      draft.activeRequestCount--;
      draft.workspace = action.payload;
      break;
    case "EXECUTE_ACTION_SUCCESS":
      draft.activeRequestCount--;
      const currentCard = getCurrentCard(draft.workspace);
      if (currentCard) {
        currentCard.next_id = action.payload.card.id;
      } else {
        console.warn("No current card in EXECUTE_ACTION_SUCCESS");
      }
      const { card, view } = action.payload;
      const newWorkspace = {
        cards: [...draft.workspace!.cards, card],
        view,
      };
      draft.workspace = newWorkspace;
      break;
    case "SET_SELECTED_CARD_ROWS":
      draft.workspace.view.selected_rows = action.payload(draft.workspace.view.selected_rows);
      break;
    case "SET_FOCUSED_ROW_INDEX":
      draft.workspace.view.focused_row_index = action.payload;
      break;
    case "UPDATE_AVAILABLE_ACTIONS_SUCCESS":
      draft.activeRequestCount--;
      draft.workspace.available_actions = action.payload;
      break;
    case "SET_CARDVIEW_CARD_ID":
      draft.workspace.view.card_id = action.payload;
      draft.workspace.view.selected_rows = {};
      break;
    default:
      return;
  }
};

// create a context object with a default value of the initial state
const WorkspaceContext = createContext(initialState);

// create a custom hook that returns the context value
export function useWorkspace() {
  const workspace = useContext(WorkspaceContext);
  return workspace;
}

// create a provider component that uses the reducer and dispatches actions
export function WorkspaceProvider({ children }) {
  const [state, dispatch] = useImmerReducer(reducer, initialState);
  const stateRef = useRef(state);

  useEffect(() => {
    fetchWorkspace();
  }, []);

  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  // create a function that dispatches a fetch request action
  const fetchWorkspace = () => {
    dispatch({ type: "FETCH_REQUEST" });
    getInitialWorkspace()
      .then(data => {
        dispatch({ type: "FETCH_WORKSPACE_SUCCESS", payload: data });
      })
      .catch(err => {
        dispatch({ type: "FETCH_FAILURE", payload: err });
      });
  };

  // create a function that dispatches an update workspace action
  const updateWorkspaceData = workspace => {
    dispatch({ type: "FETCH_REQUEST" });
    updateWorkspace({ workspace })
      .then(data => {
        dispatch({ type: "UPDATE_WORKSPACE_SUCCESS", payload: data });
      })
      .catch(err => {
        dispatch({ type: "FETCH_FAILURE", payload: err });
      });
  };

  const executeAction = action => {
    dispatch({ type: "FETCH_REQUEST" });
    const cardWithView = getCurrentCardWithView(stateRef.current.workspace);
    if (!cardWithView) {
      return;
    }
    const { card, view } = cardWithView;
    console.log("executeAction", { card, view, action });
    apiExecuteAction({ card, view, action })
      .then(data => {
        dispatch({ type: "EXECUTE_ACTION_SUCCESS", payload: data });
        updateAvailableActions();
      })
      .catch(err => {
        dispatch({ type: "FETCH_FAILURE", payload: err });
      });
  };

  const updateAvailableActions = () => {
    dispatch({ type: "FETCH_REQUEST" });
    const cardWithView = getCurrentCardWithView(stateRef.current.workspace);
    if (!cardWithView) {
      return;
    }
    const { card, view } = cardWithView;
    getAvailableActions({ card, view })
      .then(data => {
        dispatch({ type: "UPDATE_AVAILABLE_ACTIONS_SUCCESS", payload: data });
      })
      .catch(err => {
        dispatch({ type: "FETCH_FAILURE", payload: err });
      });
  };

  const setSelectedCardRows = rowUpdateFn => {
    dispatch({ type: "SET_SELECTED_CARD_ROWS", payload: rowUpdateFn });
    updateAvailableActions();
  };

  const setFocusedCardRow = rowIndexOrUpdateFn => {
    const rowIndex =
      typeof rowIndexOrUpdateFn === "function"
        ? rowIndexOrUpdateFn(stateRef.current.workspace.view.focused_row_index)
        : rowIndexOrUpdateFn;
    dispatch({ type: "SET_FOCUSED_ROW_INDEX", payload: rowIndex });
    updateAvailableActions();
  };

  const setCardViewCard = cardId => {
    dispatch({ type: "SET_CARDVIEW_CARD_ID", payload: cardId });
    updateAvailableActions();
  };

  return (
    <WorkspaceContext.Provider
      value={{
        ...state,
        updateWorkspaceData,
        setSelectedCardRows,
        setFocusedCardRow,
        setCardViewCard,
        executeAction,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}
