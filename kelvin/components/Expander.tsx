import React, { useState } from "react";

function Expander({ openLabel, closedLabel, content }) {
  // Use state to track whether the expander is open or closed
  const [open, setOpen] = useState(false);

  // Define a function to toggle the open state
  const toggle = () => {
    setOpen(prev => !prev);
  };

  // Use tailwind classes to style the expander and the label
  return (
    <div className="max-w-1/2">
      {/* Use a button to trigger the toggle function and show an icon based on the open state */}
      <button
        className="flex items-center justify-between w-full p-1 border border-gray-300 rounded"
        onClick={toggle}
      >
        <span className="text-gray-700">{open ? openLabel : closedLabel}</span>
        <span className="text-gray-500">
          {open ? (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 15l7-7 7 7"
              />
            </svg>
          ) : (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          )}
        </span>
      </button>
      {/* Use a conditional rendering to show or hide the label based on the open state */}
      {open && (
        <pre className="m-t-5 max-w-1/2 whitespace-pre-wrap p-2 bg-gray-100 rounded">{content}</pre>
      )}
    </div>
  );
}

export default Expander;
