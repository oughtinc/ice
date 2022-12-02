import Expander from "./Expander";
import { Action as ActionType } from "/types";

const Action = ({ kind, params, label }: ActionType) => {
  if (kind == "DebugAction") {
    return (
      <div className="action">
        <Expander openLabel="Hide prompt" closedLabel="Show prompt" content={label} />
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
