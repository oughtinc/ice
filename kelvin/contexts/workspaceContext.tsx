import React, { createContext, useContext, useEffect, useRef } from "react";
import { useImmerReducer } from "use-immer";
import {
  executeAction as apiExecuteAction,
  getAvailableActions,
  getInitialWorkspace,
} from "../api";
import { PartialFrontier, Workspace } from "../types";
import { getFocusPath, getFrontier, updateWorkspace } from "/utils/workspace";

type State = {
  workspace: Workspace | null;
  error: Error | null;
  activeRequestCount: number;
};

type ReducerAction =
  | { type: "FETCH_REQUEST" }
  | { type: "FETCH_FAILURE"; payload: Error }
  | { type: "FETCH_WORKSPACE_SUCCESS"; payload: Workspace }
  | { type: "EXECUTE_ACTION_SUCCESS"; payload: PartialFrontier }
  | {
      type: "SET_FOCUSED_ROW_INDEX";
      payload: number;
    }
  | {
      type: "SET_SELECTED_ROW_IDS";
      payload: (rows: Record<string, boolean>) => Record<string, boolean>;
    }
  | { type: "UPDATE_AVAILABLE_ACTIONS_SUCCESS"; payload: Action[] }
  | { type: "SET_FOCUS_PATH_HEAD_CARD_ID"; payload: string };

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
    case "EXECUTE_ACTION_SUCCESS":
      draft.activeRequestCount--;
      console.log("EXECUTE_ACTION_SUCCESS", action.payload); // not getting text prop here
      draft.workspace = updateWorkspace(draft.workspace, action.payload);
      break;
    case "UPDATE_AVAILABLE_ACTIONS_SUCCESS":
      draft.activeRequestCount--;
      draft.workspace.available_actions = action.payload;
      break;
    case "SET_SELECTED_ROW_IDS": {
      const focus_path = getFocusPath(draft.workspace);
      focus_path.view.selected_row_ids = action.payload(focus_path.view.selected_row_ids);
      console.log("selected_row_ids", focus_path.view.selected_row_ids);
      break;
    }
    case "SET_FOCUSED_ROW_INDEX": {
      const focus_path = getFocusPath(draft.workspace);
      focus_path.view.focused_row_index = action.payload;
      break;
    }
    case "SET_FOCUS_PATH_HEAD_CARD_ID": {
      const focus_path = getFocusPath(draft.workspace);
      focus_path.head_card_id = action.payload;
      focus_path.view.focused_row_index = 0;
      break;
    }
    default:
      return;
  }
};

const WorkspaceContext = createContext(initialState);

export function useWorkspace() {
  const workspace = useContext(WorkspaceContext);
  return workspace;
}

export function WorkspaceProvider({ children }) {
  const [state, dispatch] = useImmerReducer(reducer, initialState);
  const stateRef = useRef(state);

  useEffect(() => {
    fetchWorkspace();
  }, []);

  useEffect(() => {
    stateRef.current = state;
  }, [state]);

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

  const executeAction = action => {
    dispatch({ type: "FETCH_REQUEST" });
    const frontier = getFrontier(stateRef.current.workspace);
    if (!frontier) {
      return;
    }
    console.log("executeAction", action, frontier);
    apiExecuteAction({ action, frontier })
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
    const frontier = getFrontier(stateRef.current.workspace);
    if (!frontier) {
      return;
    }
    console.log("updateAvailableActions", frontier);
    getAvailableActions({ frontier })
      .then(data => {
        dispatch({ type: "UPDATE_AVAILABLE_ACTIONS_SUCCESS", payload: data });
      })
      .catch(err => {
        dispatch({ type: "FETCH_FAILURE", payload: err });
      });
  };

  const setSelectedCardRows = rowUpdateFn => {
    dispatch({ type: "SET_SELECTED_ROW_IDS", payload: rowUpdateFn });
    updateAvailableActions();
  };

  const setFocusedCardRow = rowIndexOrUpdateFn => {
    if (typeof rowIndexOrUpdateFn === "function") {
      const workspace = stateRef.current.workspace;
      const focus_path = workspace.paths[workspace.focus_path_id];
      const rowIndex = rowIndexOrUpdateFn(focus_path.view.focused_row_index);
      dispatch({ type: "SET_FOCUSED_ROW_INDEX", payload: rowIndex });
    } else {
      const rowIndex = rowIndexOrUpdateFn;
      dispatch({ type: "SET_FOCUSED_ROW_INDEX", payload: rowIndex });
    }
    updateAvailableActions();
  };

  const setFocusPathHeadCardId = cardId => {
    dispatch({ type: "SET_FOCUS_PATH_HEAD_CARD_ID", payload: cardId });
    updateAvailableActions();
  };

  return (
    <WorkspaceContext.Provider
      value={{
        ...state,
        setSelectedCardRows,
        setFocusedCardRow,
        setFocusPathHeadCardId,
        executeAction,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}
