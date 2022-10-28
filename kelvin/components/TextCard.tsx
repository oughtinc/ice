import { TextCard as TextCardType } from "../types";

type Props = {
  card: TextCardType;
};

const TextCard = ({ card }: Props) => {
  return (
    <div className="rounded-md pl-8">
      <ol>
        {card.rows.map((row, index) => (
          <li key={index}>{row}</li>
        ))}
      </ol>
    </div>
  );
};

export default TextCard;
