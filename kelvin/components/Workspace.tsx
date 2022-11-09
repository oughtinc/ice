import { useEffect, useState } from "react";
import { useHotkeys } from "react-hotkeys-hook";
import Action from "./Action";
import ActionForm from "./ActionForm";
import CardRow from "./CardRow";
import { Pane, Panes, usePaneSwitch } from "./Panes";
import SelectionList from "./SelectionList";
import StatusBar from "./StatusBar";
import { useWorkspace } from "/contexts/workspaceContext";
import {
  getCurrentActions,
  getCurrentCard,
  getFocusIndex,
  getSelectedCardRows,
} from "/utils/workspace";

const useActionHotkeys = (actions, executeActionAndDeselectAll, actionToPrepare) => {
  const labelFromKey = {
    a: "Add bullet point to card",
    c: "Clear card",
    e: "Edit text",
    m: "Run language model",
  };

  const actionMatchesLabel = (action, label) => {
    return action.label.toLowerCase().startsWith(label.toLowerCase());
  };

  for (const [key, label] of Object.entries(labelFromKey)) {
    useHotkeys(
      key,
      () => {
        if (!actionToPrepare) {
          const action = actions.find(action => actionMatchesLabel(action, label));
          if (action) {
            executeActionAndDeselectAll(action);
          }
        }
      },
      [actionToPrepare, executeActionAndDeselectAll, actions],
    );
  }

  const actionKeys = actions.map(action => {
    const key = Object.keys(labelFromKey).find(key =>
      actionMatchesLabel(action, labelFromKey[key]),
    );
    return key;
  });

  return { actionKeys };
};

const Workspace = () => {
  const {
    workspace,
    executeAction,
    setSelectedCardRows,
    setFocusedCardRow,
    activeRequestCount,
    error,
  } = useWorkspace();

  const [baseActivePane, setActivePane, LEFT_PANE, RIGHT_PANE] = usePaneSwitch();
  const [selectedActions, setSelectedActions] = useState({});
  const [actionFocusIndex, setActionFocusIndex] = useState(0);
  const [actionToPrepare, setActionToPrepare] = useState(null);

  const card = getCurrentCard(workspace);
  const actions = getCurrentActions(workspace) || [];
  const selectedCardRows = getSelectedCardRows(workspace);
  const cardFocusIndex = getFocusIndex(workspace) || 0;

  const activePane = card && !card.rows.length && actions ? RIGHT_PANE : baseActivePane;

  const executeActionAndDeselectAll = action => {
    if (action.params.every(param => param.value !== null)) {
      executeAction(action);
      setSelectedCardRows(() => ({}));
      setActionToPrepare(null);
      setActivePane(LEFT_PANE);
    } else {
      setActivePane(RIGHT_PANE);
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

  useEffect(() => {
    setActionFocusIndex(0);
  }, [cardFocusIndex, actions]);

  const { actionKeys } = useActionHotkeys(actions, executeActionAndDeselectAll, actionToPrepare);

  return (
    <Panes>
      <Pane active={activePane === LEFT_PANE}>
        <SelectionList
          name="Card"
          multiselect={true}
          items={card?.rows || []}
          selected={selectedCardRows}
          setSelected={setSelectedCardRows}
          onEnter={() => setActivePane(RIGHT_PANE)}
          active={activePane === LEFT_PANE}
          renderItem={row => <CardRow cardKind={card?.kind} row={row} />}
          focusIndex={cardFocusIndex}
          setFocusIndex={setFocusedCardRow}
        />
      </Pane>
      <Pane active={activePane === RIGHT_PANE}>
        {actionToPrepare ? (
          <ActionForm partialAction={actionToPrepare} onSubmit={executeActionAndDeselectAll} />
        ) : (
          <SelectionList
            name="Actions"
            multiselect={false}
            items={actions}
            keys={actionKeys}
            selected={selectedActions}
            setSelected={setSelectedActions}
            onEnter={executeActionAndDeselectAll}
            active={activePane === RIGHT_PANE}
            renderItem={action => <Action {...action} />}
            focusIndex={actionFocusIndex}
            setFocusIndex={setActionFocusIndex}
          />
        )}
      </Pane>
      <StatusBar activeRequestCount={activeRequestCount} error={error} />
    </Panes>
  );
};

export default Workspace;
