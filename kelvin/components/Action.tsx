import { Action as ActionType } from "/types";

const Action = ({ kind, params, label }: ActionType) => {
  return (
    <div className="action">
      <span className="action-label">{label}</span>
    </div>
  );
};

export default Action;
