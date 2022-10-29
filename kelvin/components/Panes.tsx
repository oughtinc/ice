import { useState } from "react";
import { useHotkeys } from "react-hotkeys-hook";

export const Pane = ({ children, active }) => {
  return (
    <div
      className={`flex-1 p-4 border border-gray-200 ${
        active ? "border-t-blue-500" : "border-t-white"
      } overflow-auto`}
    >
      {children}
    </div>
  );
};

export const Panes = ({ children }) => {
  return <div className="flex h-screen">{children}</div>;
};

// A custom hook that manages the pane switching logic
export const usePaneSwitch = (initialPane = "left") => {
  // Use constants or enums for the pane names
  const LEFT_PANE = "left";
  const RIGHT_PANE = "right";

  // Use state to keep track of the active pane
  const [activePane, setActivePane] = useState(initialPane);

  // Use hotkeys to handle pane switching
  useHotkeys(
    "left, h",
    () => {
      // Set the active pane to left
      setActivePane(LEFT_PANE);
    },
    {},
    [setActivePane],
  );

  useHotkeys(
    "right, l",
    () => {
      // Set the active pane to right
      setActivePane(RIGHT_PANE);
    },
    {},
    [setActivePane],
  );

  return [activePane, setActivePane, LEFT_PANE, RIGHT_PANE];
};
