import { useEffect, useState } from "react";
import { useHotkeys } from "react-hotkeys-hook";
import Action from "./Action";
import ActionForm from "./ActionForm";
import CardRow from "./CardRow";
import { Pane, Panes } from "./Panes";
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
  // Todo: This should be stored in workspace
  const labelFromKey = {
    a: "Add bullet point to card",
    c: "Clear card",
    e: "Edit text",
    m: "Run language model",
    p: "Search papers",
    v: "View paper",
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

  const assignedKeys = new Set();
  const actionKeys = actions.map(action => {
    const key = Object.keys(labelFromKey).find(key =>
      actionMatchesLabel(action, labelFromKey[key]),
    );
    if (key) {
      if (assignedKeys.has(key)) {
        return null;
      } else {
        assignedKeys.add(key);
        return key;
      }
    }
    return null;
  });

  return { actionKeys };
};

const Workspace = () => {
  const {
    workspace,
    executeAction,
    setSelectedCardRows,
    setFocusedCardRow,
    setCardViewCard,
    activeRequestCount,
    error,
  } = useWorkspace();

  const LEFT_PANE = "left";
  const RIGHT_PANE = "right";

  const [baseActivePane, setActivePane] = useState(RIGHT_PANE);

  const [selectedActions, setSelectedActions] = useState({});
  const [actionFocusIndex, setActionFocusIndex] = useState(0);
  const [actionToPrepare, setActionToPrepare] = useState(null);

  const card = getCurrentCard(workspace);
  const actions = getCurrentActions(workspace) || [];
  const selectedCardRows = getSelectedCardRows(workspace);
  const cardFocusIndex = getFocusIndex(workspace) || 0;

  const activePane = card && !card.rows.length && actions ? RIGHT_PANE : baseActivePane;
  // const activePane = baseActivePane;

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

  useHotkeys(
    "left, h",
    () => {
      if (card && card.prev_id) {
        setCardViewCard(card.prev_id);
      }
    },
    {},
    [setCardViewCard, card],
  );

  useHotkeys(
    "right, l",
    () => {
      if (card && card.next_id) {
        console.log(card.next_id);
        setCardViewCard(card.next_id);
      }
    },
    {},
    [setCardViewCard, card],
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
