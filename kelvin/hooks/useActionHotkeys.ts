import { useHotkeys } from "react-hotkeys-hook";

const useActionHotkeys = ({ actions, executeActionAndDeselectAll, actionToPrepare }) => {
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

export default useActionHotkeys;
