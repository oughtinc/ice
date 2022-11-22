import { Action as ActionType } from "/types";

const Action = ({ kind, params, label }: ActionType) => {
  if (kind == "DebugAction") {
    return (
      <div className="action">
        <pre className="max-w-1/2 whitespace-pre-wrap">{label}</pre>
      </div>
    );
  }
  return (
    <div className="action">
      <span className="action-label">{label}</span>
    </div>
  );
};

export default Action;
