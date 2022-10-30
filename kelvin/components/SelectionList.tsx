import { useState } from "react";
import { useHotkeys } from "react-hotkeys-hook";

const SelectionListItem = ({
  item,
  focus,
  selected,
  setItemSelection,
  onEnter,
  active,
  renderItem,
}) => {
  // Use hotkeys to handle toggle and enter
  useHotkeys(
    "space",
    () => {
      console.log("space", { item, selected });
      setItemSelection(item, "toggle");
    },
    { enabled: active && focus },
    [active, item.id],
  );

  useHotkeys(
    "enter",
    () => {
      // Invoke the onEnter callback with the item
      console.log("enter", { item });
      onEnter(item); // call the original onEnter prop
      setItemSelection(item, true);
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
    <li className={`flex p-1 pl-2 pr-2 items-baseline ${bgColor}`}>
      <span className={`mr-2 ${selected ? "text-blue-500" : "text-black"}`}>•</span>
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

const SelectionList = ({ name, items, onEnter, active, renderItem, selected, setSelected }) => {
  const [focusIndex, focusId] = useFocusIndex({ name, items, active });

  const setItemSelection = (item, value) => {
    if (value === "toggle") {
      setSelected(prev => ({ ...prev, [item.id]: !prev[item.id] }));
    } else {
      setSelected(prev => ({ ...prev, [item.id]: value }));
    }
  };

  return (
    <ul className="list-disc list-inside">
      {items.map(item => (
        <SelectionListItem
          key={item.id}
          item={item}
          focus={item.id === focusId}
          selected={selected[item.id]}
          setItemSelection={setItemSelection}
          onEnter={onEnter}
          active={active}
          renderItem={renderItem}
        />
      ))}
    </ul>
  );
};

export default SelectionList;
