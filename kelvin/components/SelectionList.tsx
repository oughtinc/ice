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
  itemKey,
  focused,
  selected,
  active,
  multiselect,
  setSelected,
  renderItem,
  forwardedRef,
}) => {
  // Use a checkmark icon instead of a bullet point
  const checkmark =
    selected || !active & focused ? (
      <svg
        className={`${selected ? "text-blue-500" : "text-gray-500"} mr-2`}
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M5.33333 10.6667L2.66667 8L1.33333 9.33333L5.33333 13.3333L14.6667 4L13.3333 2.66667L5.33333 10.6667Z"
          fill="currentColor"
        />
      </svg>
    ) : (
      // Use an empty checkmark icon on hover
      <svg
        className={`text-gray-400 mr-2 ${focused ? "opacity-100" : "opacity-0"}`}
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <rect x="0.5" y="0.5" width="15" height="15" rx="2.5" stroke="currentColor" />
      </svg>
    );

  const bullet = <div className="w-3">•</div>;

  // Use a consistent background color for focused and selected items
  const bgColor = focused ? "bg-blue-200" : selected ? "bg-blue-100" : "";

  // Use a different background color and text color for the keyboard shortcut depending on the focus state
  const kbdBgColor = focused ? "bg-gray-100" : "bg-white";
  const kbdTextColor = focused ? "text-gray-700" : "text-gray-500";

  return (
    <li className={`flex p-1 pl-2 pr-2 items-center ${bgColor}`} ref={forwardedRef}>
      {multiselect ? checkmark : bullet} <div className="flex-grow">{renderItem(item)}</div>
      <kbd
        className={`font-mono ml-2 px-1.5 border border-gray-300 rounded-md ${kbdBgColor} ${kbdTextColor} ${
          !itemKey && "opacity-0"
        }`}
      >
        {itemKey || "x"}
      </kbd>
    </li>
  );
};

const SelectionList = ({
  name,
  items,
  keys,
  multiselect,
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
    "space, x",
    () => {
      const item = items[focusIndex];
      if (item) {
        setSelected(prev => ({ ...prev, [item.id]: !prev[item.id] }));
      }
    },
    { enabled: active && multiselect },
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
      setFocusIndex(prev => Math.max((prev || 0) - 1, 0));
    },
    { enabled: active },
    [items, active],
  );

  useHotkeys(
    "down, j",
    () => {
      setFocusIndex(prev => Math.min((prev || 0) + 1, items.length - 1));
    },
    { enabled: active },
    [items, active],
  );

  // Detect the platform and the modifier key
  const isMac =
    typeof window !== "undefined" ? window.navigator.platform.toLowerCase().includes("mac") : false;
  const modifierKey = isMac ? "command" : "ctrl";

  useHotkeys(
    `${modifierKey}+a`,
    event => {
      event.preventDefault();
      setSelected(draft => {
        items.forEach(item => {
          draft[item.id] = true;
        });
        return draft;
      });
      setFocusIndex(items.length - 1);
    },
    { enabled: active },
    [items, active, selected],
  );

  return (
    <ul className="list-disc list-inside">
      {items.map((item, i) => (
        <SelectionListItem
          key={item.id}
          item={item}
          itemKey={keys && keys[i]}
          multiselect={multiselect}
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
