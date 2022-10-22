import Card from "./Card";
import Action from "./Action";
import { Workspace } from "../types";

type Props = {
  workspace: Workspace;
};

const CurrentCard = ({ workspace }: Props) => {
  const { currentCardId, cards } = workspace;
  const currentCard = cards[currentCardId];
  return <Card card={currentCard} />;
};

export default CurrentCard;
