import Head from "next/head";
import { useEffect } from "react";
import { useImmerReducer } from "use-immer";

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

type Card<T> = {
  rows: T[];
};

type TextCard = Card<string>;

type Action = {
  action_type: "ask_question";
  action_param_types: { [key: string]: string };
  action_param_values: { [key: string]: any };
};

type QuestionAction = {
  action_type: "ask_question";
  action_param_types: { question: "text" };
  action_param_values: { question?: string };
};

type ActionCard = Card<Action>;

type Workspace = {
  cards: { [string]: Card };
  currentCardId: string;
};

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

const CurrentCard = ({ workspace }: { workspace: Workspace }) => {
  const { currentCardId, cards } = workspace;
  const currentCard = cards[currentCardId];
  return <pre>{JSON.stringify(currentCard)}</pre>;
};

export default function HomePage() {
  const [state, dispatch] = useImmerReducer(reducer, initialState);

  const { workspace, loading, error } = state;

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

  return (
    <div className="m-8">
      <Head>
        <title>Kelvin</title>
      </Head>
      {loading && <p>Loading...</p>}
      {error && <p>Error: {error.message}</p>}
      {!loading && workspace && <CurrentCard workspace={workspace} />}
    </div>
  );
}
