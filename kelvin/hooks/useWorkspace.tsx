import { useEffect } from "react";
import { useImmerReducer } from "use-immer";
import { Workspace } from "../types";

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8935";

type State = {
  workspace: Workspace | null;
  loading: boolean;
  error: Error | null;
};

type ReducerAction =
  | { type: "FETCH_REQUEST" }
  | { type: "FETCH_FAILURE"; payload: Error }
  | { type: "FETCH_WORKSPACE_SUCCESS"; payload: Workspace };

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
    default:
      return;
  }
};

const useWorkspace = () => {
  const [state, dispatch] = useImmerReducer(reducer, initialState);

  const fetchInitialWorkspace = async () => {
    dispatch({ type: "FETCH_REQUEST" });
    try {
      const response = await fetch(`${backendUrl}/kelvin/workspaces/initial`);
      const data = await response.json();
      dispatch({ type: "FETCH_WORKSPACE_SUCCESS", payload: data });
    } catch (err) {
      dispatch({ type: "FETCH_FAILURE", payload: err });
    }
  };

  useEffect(() => {
    fetchInitialWorkspace();
  }, []);

  return state;
};

export default useWorkspace;
