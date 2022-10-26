import Card from "./Card";
import { useWorkspace } from "/contexts/workspaceContext";

const Workspace = () => {
  const { workspace, loading, error } = useWorkspace();
  if (loading) {
    return <div>Loading...</div>;
  }
  if (error) {
    return <div>Error: {error.message}</div>;
  }
  if (!workspace) {
    return <div>Workspace not found</div>;
  }
  const { currentCardId, cards } = workspace;
  if (!cards) {
    return <div>Workspace has no cards</div>;
    console.log({ workspace });
  }
  const currentCard = cards.find(card => card.id === currentCardId);
  if (!currentCard) {
    return <div>No card found for id {currentCardId}</div>;
  }
  return <Card card={currentCard} />;
};

export default Workspace;
