import Param from "./Param";
import { Action as ActionType } from "../types";

type Props = {
  action: ActionType;
};

const Action = ({ action }: Props) => {
  return (
    <div className="flex items-center space-x-2">
      <span className="font-bold">{action.kind}</span>
      {action.params.map((param, index) => (
        <Param key={index} param={param} />
      ))}
    </div>
  );
};

export default Action;
