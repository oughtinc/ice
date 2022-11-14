import { useEffect, useState } from "react";
import { useHotkeys } from "react-hotkeys-hook";
import Action from "./Action";
import ActionForm from "./ActionForm";
import CardRow from "./CardRow";
import { Pane, Panes } from "./Panes";
import SelectionList from "./SelectionList";
import StatusBar from "./StatusBar";
import { useWorkspace } from "/contexts/workspaceContext";
import useActionHotkeys from "/hooks/useActionHotkeys";
import { getAvailableActions, getCurrentCard, getFocusIndex, getFocusPath } from "/utils/workspace";

const Workspace = () => {
  const {
    workspace,
    executeAction,
    setSelectedCardRows,
    setFocusedCardRow,
    setFocusPathHeadCardId,
    activeRequestCount,
    error,
  } = useWorkspace();

  const LEFT_PANE = "left";
  const RIGHT_PANE = "right";

  const [baseActivePane, setActivePane] = useState(RIGHT_PANE);
  const [actionFocusIndex, setActionFocusIndex] = useState(0);
  const [actionToPrepare, setActionToPrepare] = useState(null);

  const card = getCurrentCard(workspace);
  const actions = getAvailableActions(workspace) || [];
  const selectedCardRows = getFocusPath(workspace)?.view?.selected_row_ids;
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
        setFocusPathHeadCardId(card.prev_id);
      }
    },
    {},
    [setFocusPathHeadCardId, card],
  );

  useHotkeys(
    "right, l",
    () => {
      if (card && card.next_id) {
        console.log(card.next_id);
        setFocusPathHeadCardId(card.next_id);
      }
    },
    {},
    [setFocusPathHeadCardId, card],
  );

  useEffect(() => {
    setActionFocusIndex(0);
  }, [cardFocusIndex, actions]);

  const { actionKeys } = useActionHotkeys({
    actions,
    executeActionAndDeselectAll,
    actionToPrepare,
  });

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
          renderItem={row => <CardRow row={row} />}
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
            selected={{}}
            setSelected={() => {}}
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
