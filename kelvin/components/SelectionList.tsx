import { createRef, useEffect, useRef } from "react";
import { useHotkeys } from "react-hotkeys-hook";

const useScrollIntoView = ({ items, focusIndex }) => {
  const itemRefs = useRef([]);
  itemRefs.current = items.map((_, i) => itemRefs.current[i] || createRef());

  useEffect(() => {
    const currentRef = itemRefs.current[focusIndex];
    if (currentRef && currentRef.current) {
      currentRef.current.scrollIntoView({ block: "nearest" });
    }
  }, [focusIndex]);

  return itemRefs;
};

const SelectionListItem = ({
  item,
  focused,
  selected,
  active,
  setSelected,
  renderItem,
  forwardedRef,
}) => {
  const bgColor = focused ? "bg-blue-200" : selected ? "bg-blue-150" : "";
  return (
    <li className={`flex p-1 pl-2 pr-2 items-baseline ${bgColor}`} ref={forwardedRef}>
      <span className={`mr-2 ${selected ? "text-blue-500" : "text-black"}`}>•</span>
      {renderItem(item)}
    </li>
  );
};

const SelectionList = ({
  name,
  items,
  onEnter,
  active,
  renderItem,
  selected,
  setSelected,
  focusIndex,
  setFocusIndex,
}) => {
  const itemRefs = useScrollIntoView({ items, focusIndex });

  useHotkeys(
    "space",
    () => {
      const item = items[focusIndex];
      if (item) {
        setSelected(prev => ({ ...prev, [item.id]: !prev[item.id] }));
      }
    },
    { enabled: active },
    [active, items, focusIndex],
  );

  useHotkeys(
    "enter",
    () => {
      const item = items[focusIndex];
      if (item) {
        onEnter(item);
      }
    },
    { enabled: active },
    [active, items, focusIndex],
  );

  useHotkeys(
    "up, k",
    () => {
      setFocusIndex(prev => ((prev || 0) - 1 + items.length) % items.length);
    },
    { enabled: active },
    [items, active],
  );

  useHotkeys(
    "down, j",
    () => {
      setFocusIndex(prev => ((prev || 0) + 1) % items.length);
    },
    { enabled: active },
    [items, active],
  );

  return (
    <ul className="list-disc list-inside">
      {items.map((item, i) => (
        <SelectionListItem
          key={item.id}
          item={item}
          focused={i === focusIndex}
          selected={selected[item.id]}
          active={active}
          setSelected={setSelected}
          renderItem={renderItem}
          forwardedRef={itemRefs.current[i]}
        />
      ))}
    </ul>
  );
};

export default SelectionList;
