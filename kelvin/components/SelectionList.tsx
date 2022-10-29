import { useState } from "react";
import { useHotkeys } from "react-hotkeys-hook";

// A component that renders a list item with a checkbox
const SelectionListItem = ({ item, focus, selected, onToggle, onEnter, active, renderItem }) => {
  // Use hotkeys to handle toggle and enter
  useHotkeys(
    "space",
    () => {
      // Invoke the onToggle callback with the item
      onToggle(item);
    },
    { enabled: active && focus },
    [active, item.id],
  );

  useHotkeys(
    "enter",
    () => {
      // Invoke the onEnter callback with the item
      console.log("enter", { item });
      onEnter(item);
    },
    { enabled: active && focus },
    [active, item.id],
  );

  // Use different background colors for selected and focus states
  let bgColor = "";
  if (focus && active) {
    bgColor = "bg-blue-200";
  } else if (selected) {
    bgColor = "bg-blue-150";
  }

  return (
    <li className={`flex items-baseline ${bgColor}`}>
      <span className="mr-2">•</span>
      {renderItem(item)}
    </li>
  );
};

const useFocusIndex = ({ name, items, initialIndex = 0, active }) => {
  const [focusIndex, setFocusIndex] = useState(initialIndex);

  useHotkeys(
    "up, k",
    () => {
      setFocusIndex(prev => (prev - 1 + items.length) % items.length);
    },
    { enabled: active },
    [active, items],
  );

  useHotkeys(
    "down, j",
    () => {
      setFocusIndex(prev => (prev + 1) % items.length);
    },
    { enabled: active },
    [active, items],
  );

  return [focusIndex, items[focusIndex]?.id];
};

const useSelection = (items, initialSelection = {}) => {
  const [selected, setSelected] = useState(initialSelection);

  const toggle = item => {
    setSelected(prev => ({
      ...prev,
      [item.id]: !prev[item.id],
    }));
  };

  return [selected, toggle];
};

const SelectionList = ({
  name,
  items,
  onEnter,
  active,
  renderItem,
  selected = null,
  setSelected = null,
}) => {
  const [focusIndex, focusId] = useFocusIndex({ name, items, active });
  const [internalSelected, internalToggle] = useSelection(items);
  const currentSelected = selected ?? internalSelected;
  const toggle = setSelected
    ? item => setSelected(prev => ({ ...prev, [item.id]: !prev[item.id] }))
    : internalToggle;

  console.log("SelectionList", { items });

  return (
    <ul className="list-disc list-inside">
      {items.map(item => (
        <SelectionListItem
          key={item.id}
          item={item}
          focus={item.id === focusId}
          selected={currentSelected[item.id]}
          onToggle={toggle}
          onEnter={onEnter}
          active={active}
          renderItem={renderItem}
        />
      ))}
    </ul>
  );
};

export default SelectionList;
