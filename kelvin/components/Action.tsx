import { useImmer } from "use-immer";
import { Action as ActionType } from "../types";
import Param from "./Param";

type Props = {
  action: ActionType;
  onSubmit: (action: ActionType) => void; // callback for executing the action
};

const actionLabels: Record<string, string> = {
  create_question_action: "Ask a research question",
};

const Action = ({ action, onSubmit }: Props) => {
  const actionLabel = actionLabels[action.kind] || action.kind;
  const [params, setParams] = useImmer(action.params);

  const updateParam = (index: number, value: string | null) => {
    setParams(draft => {
      console.log({ index, value, draft });
      draft[index].value = value;
      return draft;
    });
  };

  const allParamsFilled = () => {
    return params.every(param => param.value !== null);
  };

  const handleSubmit = () => {
    if (allParamsFilled()) {
      onSubmit({ ...action, params }); // pass the updated action to the callback
    }
  };

  return (
    <div className="flex items-center space-x-2">
      <span className="font-bold">{actionLabel}</span>
      {params.map((param, index) => (
        <Param key={index} param={param} onChange={value => updateParam(index, value)} />
      ))}
      <button
        className="bg-blue-500 text-white px-4 py-2 rounded-md"
        disabled={!allParamsFilled()}
        onClick={handleSubmit}
      >
        Submit
      </button>
    </div>
  );
};

export default Action;
