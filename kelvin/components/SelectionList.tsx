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
  index,
}) => {
  const bullet = <div className="w-3">•</div>;

  let icon;
  switch (item.kind) {
    case "Text":
      icon = (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          className="w-5 h-5"
        >
          <path
            fillRule="evenodd"
            d="M10 2c-2.236 0-4.43.18-6.57.524C1.993 2.755 1 4.014 1 5.426v5.148c0 1.413.993 2.67 2.43 2.902 1.168.188 2.352.327 3.55.414.28.02.521.18.642.413l1.713 3.293a.75.75 0 001.33 0l1.713-3.293a.783.783 0 01.642-.413 41.102 41.102 0 003.55-.414c1.437-.231 2.43-1.49 2.43-2.902V5.426c0-1.413-.993-2.67-2.43-2.902A41.289 41.289 0 0010 2zM6.75 6a.75.75 0 000 1.5h6.5a.75.75 0 000-1.5h-6.5zm0 2.5a.75.75 0 000 1.5h3.5a.75.75 0 000-1.5h-3.5z"
            clipRule="evenodd"
          />
        </svg>
      );
      break;
    case "Paper":
      icon = (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          className="w-5 h-5"
        >
          <path d="M10.75 16.82A7.462 7.462 0 0115 15.5c.71 0 1.396.098 2.046.282A.75.75 0 0018 15.06v-11a.75.75 0 00-.546-.721A9.006 9.006 0 0015 3a8.963 8.963 0 00-4.25 1.065V16.82zM9.25 4.065A8.963 8.963 0 005 3c-.85 0-1.673.118-2.454.339A.75.75 0 002 4.06v11a.75.75 0 00.954.721A7.506 7.506 0 015 15.5c1.579 0 3.042.487 4.25 1.32V4.065z" />
        </svg>
      );
      break;
    case "PaperSection":
      icon = (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          className="w-5 h-5"
        >
          <path
            fillRule="evenodd"
            d="M10 2c-1.716 0-3.408.106-5.07.31C3.806 2.45 3 3.414 3 4.517V17.25a.75.75 0 001.075.676L10 15.082l5.925 2.844A.75.75 0 0017 17.25V4.517c0-1.103-.806-2.068-1.93-2.207A41.403 41.403 0 0010 2z"
            clipRule="evenodd"
          />
        </svg>
      );
      break;
    default:
      icon = bullet; // default to the bullet icon if no kind is specified
  }

  // Use a checkmark icon instead of a bullet point
  const checkmark = selected ? ( //  || !active & focused
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
    // Display an icon
    // Display item based on item.kind
    // item.kind can be Text, Paper, PaperSection, or other
    icon
  );

  const bolt = (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 20 20"
      fill="currentColor"
      className="w-5 h-5"
    >
      <path d="M11.983 1.907a.75.75 0 00-1.292-.657l-8.5 9.5A.75.75 0 002.75 12h6.572l-1.305 6.093a.75.75 0 001.292.657l8.5-9.5A.75.75 0 0017.25 8h-6.572l1.305-6.093z" />
    </svg>
  );

  const iconElement = multiselect ? checkmark : bolt;

  // Use a consistent background color for focused and selected items
  const bgColor = focused ? "bg-blue-200" : selected ? "bg-blue-100" : "";

  // Use a different background color and text color for the keyboard shortcut depending on the focus state
  const kbdBgColor = focused ? "bg-gray-100" : "bg-white";
  const kbdTextColor = focused ? "text-gray-700" : "text-gray-500";

  const keyElement = (
    <kbd
      className={`font-mono ml-2 px-1.5 border border-gray-300 rounded-md ${kbdBgColor} ${kbdTextColor} ${
        !itemKey && "opacity-0"
      }`}
    >
      {itemKey || "x"}
    </kbd>
  );

  const iconColor = active && focused ? "text-yellow-400" : "text-slate-400";

  return (
    <li className={`flex p-1 pl-2 pr-2 items-center ${bgColor}`} ref={forwardedRef}>
      <div className={`w-8 flex-shrink-0 ${iconColor}`}>{iconElement}</div>
      <div className="flex-grow">{renderItem(item)}</div>
      {keyElement}
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
    "space",
    () => {
      const item = items[focusIndex];
      if (item) {
        setSelected(prev => ({ ...prev, [item.id]: !prev[item.id] }));
      }
    },
    { enabled: active && multiselect, preventDefault: true },
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
    { enabled: active, preventDefault: true },
    [active, items, focusIndex],
  );

  useHotkeys(
    "up, k",
    () => {
      setFocusIndex(prev => Math.max((prev || 0) - 1, 0));
    },
    { enabled: active, preventDefault: true },
    [items, active],
  );

  useHotkeys(
    "down, j",
    () => {
      setFocusIndex(prev => Math.min((prev || 0) + 1, items.length - 1));
    },
    { enabled: active, preventDefault: true },
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
          key={i}
          item={item}
          itemKey={keys && keys[i]}
          multiselect={multiselect}
          focused={i === focusIndex}
          selected={selected[item.id]}
          active={active}
          setSelected={setSelected}
          renderItem={renderItem}
          forwardedRef={itemRefs.current[i]}
          index={i}
        />
      ))}
    </ul>
  );
};

export default SelectionList;
