import { Action as ActionType } from "../types";
import Action from "./Action";
import Card from "./Card";
import Error from "./Error";
import Loading from "./Loading";
import NotFound from "./NotFound";
import { useWorkspace } from "/contexts/workspaceContext";

function useCurrentCard(workspace: Workspace | null) {
  if (!workspace) return null;
  const { cards, view } = workspace;
  return cards.find(card => card.id === view.card_id);
}

const Workspace = () => {
  const { workspace, executeAction, loading, error } = useWorkspace();

  const currentCard = useCurrentCard(workspace);

  if (loading) return <Loading />;
  if (error) return <Error error={error} />;
  if (!workspace) return <NotFound message="Workspace not found" />;
  if (!currentCard) return <NotFound message={`No card found for id ${workspace.view.card_id}`} />;

  const { view } = workspace;
  const actions = view.available_actions;
  return (
    <div class="flex h-screen">
      <div class="flex-1 p-4 bg-gray-100 mr-2">
        <Card card={currentCard} />
      </div>
      <div class="flex-1 p-4 overflow-auto bg-gray-100 ml-2">
        {actions.map((row, index) => (
          <Action
            key={index}
            action={row}
            onSubmit={(action: ActionType) => {
              executeAction(action);
            }}
          />
        ))}
      </div>
    </div>
  );
};

export default Workspace;
