import { Action as ActionType, ActionCard as ActionCardType } from "../types";
import Action from "./Action";

type Props = {
  card: ActionCardType;
};

const ActionCard = ({ card }: Props) => {
  return (
    <div className="bg-blue-100 p-4 rounded-md">
      {card.rows.map((row, index) => (
        <Action
          key={index}
          action={row}
          onSubmit={(action: ActionType) => {
            console.log(`Submitted action`, action);
          }}
        />
      ))}
    </div>
  );
};

export default ActionCard;
