import Action from "./Action";
import { ActionCard as ActionCardType } from "../types";

type Props = {
  card: ActionCardType;
};

const ActionCard = ({ card }: Props) => {
  return (
    <div className="bg-blue-100 p-4 rounded-md">
      {card.rows.map((row, index) => (
        <Action key={index} action={row} />
      ))}
    </div>
  );
};

export default ActionCard;
