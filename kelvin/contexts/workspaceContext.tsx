import React, { createContext, useContext, useEffect, useRef } from "react";
import { useImmerReducer } from "use-immer";
import {
  executeAction as apiExecuteAction,
  getAvailableActions,
  getInitialWorkspace,
  updateWorkspace,
} from "../api";
import { Workspace } from "../types";
import { getCurrentCardWithView } from "/utils/workspace";

type State = {
  workspace: Workspace | null;
  loading: boolean;
  error: Error | null;
};

type ReducerAction =
  | { type: "FETCH_REQUEST" }
  | { type: "FETCH_FAILURE"; payload: Error }
  | { type: "FETCH_WORKSPACE_SUCCESS"; payload: Workspace }
  | { type: "UPDATE_WORKSPACE_SUCCESS"; payload: Workspace }
  | { type: "EXECUTE_ACTION_SUCCESS"; payload: Workspace }
  | {
      type: "SET_SELECTED_CARD_ROWS";
      payload: (rows: Record<string, boolean>) => Record<string, boolean>;
    }
  | { type: "UPDATE_AVAILABLE_ACTIONS_SUCCESS"; payload: Action[] };

const initialState: State = {
  workspace: null,
  loading: false,
  error: null,
};

const reducer = (draft: State, action: ReducerAction) => {
  switch (action.type) {
    case "FETCH_REQUEST":
      draft.loading = true;
      draft.error = null;
      break;
    case "FETCH_FAILURE":
      draft.loading = false;
      draft.error = action.payload;
      break;
    case "FETCH_WORKSPACE_SUCCESS":
      draft.loading = false;
      draft.workspace = action.payload;
      break;
    case "UPDATE_WORKSPACE_SUCCESS":
      draft.loading = false;
      draft.workspace = action.payload;
      break;
    case "EXECUTE_ACTION_SUCCESS":
      const { card, view } = action.payload;
      const newWorkspace = {
        cards: [...draft.workspace!.cards, card],
        view,
      };
      draft.loading = false;
      draft.workspace = newWorkspace;
      break;
    case "SET_SELECTED_CARD_ROWS":
      draft.workspace.view.selected_rows = action.payload(draft.workspace.view.selected_rows);
      break;
    case "UPDATE_AVAILABLE_ACTIONS_SUCCESS":
      draft.loading = false;
      draft.workspace.available_actions = action.payload;
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
    console.log("updateAvailableActions", cardWithView);
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

  return (
    <WorkspaceContext.Provider
      value={{ ...state, updateWorkspaceData, setSelectedCardRows, executeAction }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}
