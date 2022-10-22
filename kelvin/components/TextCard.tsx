import { TextCard as TextCardType } from "../types";

type Props = {
  card: TextCardType;
};

const TextCard = ({ card }: Props) => {
  return (
    <div className="bg-gray-100 p-4 rounded-md">
      {card.rows.map((row, index) => (
        <p key={index}>{row}</p>
      ))}
    </div>
  );
};

export default TextCard;
