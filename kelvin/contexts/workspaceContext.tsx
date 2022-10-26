import React, { createContext, useContext, useEffect } from "react";
import { useImmerReducer } from "use-immer";
import { executeAction as apiExecuteAction, getInitialWorkspace, updateWorkspace } from "../api";
import { Workspace } from "../types";

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
  | { type: "EXECUTE_ACTION_SUCCESS"; payload: Workspace };

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
      draft.loading = false;
      draft.workspace = action.payload;
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

  useEffect(() => {
    // fetch the workspace data on mount
    dispatch({ type: "FETCH_REQUEST" });
    getInitialWorkspace()
      .then(data => {
        dispatch({ type: "FETCH_WORKSPACE_SUCCESS", payload: data });
      })
      .catch(err => {
        dispatch({ type: "FETCH_FAILURE", payload: err });
      });
  }, []);

  // create a callback function that updates the workspace data on the API and dispatches a reducer action
  const updateWorkspaceData = newData => {
    // optionally, show some loading indicator
    dispatch({ type: "FETCH_REQUEST" });
    updateWorkspace(newData)
      .then(data => {
        // dispatch an action with the new data
        dispatch({ type: "UPDATE_WORKSPACE_SUCCESS", payload: data });
      })
      .catch(err => {
        dispatch({ type: "FETCH_FAILURE", payload: err });
      });
  };

  // create a callback function that executes an action on the API and dispatches a reducer action
  const executeAction = action => {
    // optionally, show some loading indicator
    dispatch({ type: "FETCH_REQUEST" });
    apiExecuteAction(state.workspace, action)
      .then(data => {
        // dispatch an action with the new data
        dispatch({ type: "EXECUTE_ACTION_SUCCESS", payload: data });
      })
      .catch(err => {
        dispatch({ type: "FETCH_FAILURE", payload: err });
      });
  };

  // render the provider component with the context value and the callback function
  return (
    <WorkspaceContext.Provider value={{ ...state, updateWorkspaceData, executeAction }}>
      {children}
    </WorkspaceContext.Provider>
  );
}
