import { createRef, forwardRef, useEffect, useRef, useState } from "react";
import { useHotkeys } from "react-hotkeys-hook";

const SelectionListItem = ({
  item,
  focus,
  selected,
  setItemSelection,
  onEnter,
  active,
  renderItem,
  forwardedRef,
}) => {
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
      console.log("enter", { item });
      onEnter(item);
      setItemSelection(item, true);
    },
    { enabled: active && focus },
    [active, item.id],
  );

  let bgColor = "";
  if (focus && active) {
    bgColor = "bg-blue-200";
  } else if (selected) {
    bgColor = "bg-blue-150";
  }

  return (
    <li className={`flex p-1 pl-2 pr-2 items-baseline ${bgColor}`} ref={forwardedRef}>
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

const SelectionListItemWithRef = forwardRef((props, ref) => (
  <SelectionListItem {...props} forwardedRef={ref} />
));

const SelectionList = ({ name, items, onEnter, active, renderItem, selected, setSelected }) => {
  const [focusIndex, focusId] = useFocusIndex({ name, items, active });

  const setItemSelection = (item, value) => {
    if (value === "toggle") {
      setSelected(prev => ({ ...prev, [item.id]: !prev[item.id] }));
    } else {
      setSelected(prev => ({ ...prev, [item.id]: value }));
    }
  };

  const itemRefs = useRef([]);
  itemRefs.current = items.map((_, i) => itemRefs.current[i] || createRef());

  useEffect(() => {
    const currentRef = itemRefs.current[focusIndex];
    console.log("scroll", { focusIndex, currentRef, itemRefs });
    if (currentRef && currentRef.current) {
      currentRef.current.scrollIntoView({ block: "nearest" });
    }
  }, [focusIndex]);

  return (
    <ul className="list-disc list-inside">
      {items.map((item, i) => (
        <SelectionListItemWithRef
          key={item.id}
          item={item}
          focus={item.id === focusId}
          selected={selected[item.id]}
          setItemSelection={setItemSelection}
          onEnter={onEnter}
          active={active}
          renderItem={renderItem}
          ref={itemRefs.current[i]}
        />
      ))}
    </ul>
  );
};

export default SelectionList;
