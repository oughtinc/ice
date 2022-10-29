import { useState } from "react";
import { useHotkeys } from "react-hotkeys-hook";
import Action from "./Action";
import ActionForm from "./ActionForm";
import { Pane, Panes, usePaneSwitch } from "./Panes";
import SelectionList from "./SelectionList";
import StatusBar from "./StatusBar";
import { useWorkspace } from "/contexts/workspaceContext";
import { getCurrentActions, getCurrentCard, getSelectedCardRows } from "/utils/workspace";

const Workspace = () => {
  const { workspace, executeAction, setSelectedCardRows, loading, error } = useWorkspace();
  const [activePane, setActivePane, LEFT_PANE, RIGHT_PANE] = usePaneSwitch();
  const [selectedActions, setSelectedActions] = useState({});
  const [actionToPrepare, setActionToPrepare] = useState(null);

  const card = getCurrentCard(workspace);
  const actions = getCurrentActions(workspace);
  const selectedCardRows = getSelectedCardRows(workspace);

  const selectCardRowAndSwitchPane = row => {
    setSelectedCardRows(prev => ({
      ...prev,
      [row.id]: true,
    }));
    setActivePane(RIGHT_PANE);
  };

  const executeActionAndDeselectAll = action => {
    if (action.params.every(param => param.value !== null)) {
      executeAction(action);
      setSelectedCardRows(() => ({}));
      setActionToPrepare(null);
      setActivePane(LEFT_PANE);
    } else {
      setActionToPrepare(action);
    }
  };

  useHotkeys(
    "escape",
    () => {
      if (activePane === LEFT_PANE) {
        setSelectedCardRows(() => ({}));
      } else {
        setSelectedActions(() => ({}));
        setActivePane(LEFT_PANE);
        setActionToPrepare(null);
      }
    },
    [activePane, setSelectedCardRows, setActivePane, LEFT_PANE],
  );

  return (
    <Panes>
      <Pane active={activePane === LEFT_PANE}>
        <SelectionList
          name="Card"
          items={card?.rows || []}
          selected={selectedCardRows}
          setSelected={setSelectedCardRows}
          onEnter={selectCardRowAndSwitchPane}
          active={activePane === LEFT_PANE}
          renderItem={row => <span>{row.text}</span>}
        />
      </Pane>
      <Pane active={activePane === RIGHT_PANE}>
        {actionToPrepare ? (
          <ActionForm partialAction={actionToPrepare} onSubmit={executeActionAndDeselectAll} />
        ) : (
          <SelectionList
            name="Actions"
            items={actions || []}
            selected={selectedActions}
            setSelected={setSelectedActions}
            onEnter={executeActionAndDeselectAll}
            active={activePane === RIGHT_PANE}
            renderItem={action => <Action {...action} />}
          />
        )}
      </Pane>
      <StatusBar loading={loading} error={error} />
    </Panes>
  );
};

export default Workspace;
