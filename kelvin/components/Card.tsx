import TextCard from "./TextCard";
import ActionCard from "./ActionCard";
import { Card as CardType } from "../types";

type Props = {
  card: CardType;
};

const Card = ({ card }: Props) => {
  switch (card.kind) {
    case "TextCard":
      return <TextCard card={card} />;
    case "ActionCard":
      return <ActionCard card={card} />;
    default:
      return <p>Unknown card type: {card.kind}</p>;
  }
};

export default Card;
