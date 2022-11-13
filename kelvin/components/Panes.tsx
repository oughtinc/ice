export const Pane = ({ children, active }) => {
  return (
    <div
      className={`flex-1 border ${active ? "opacity-100" : "bg-gray-100 opacity-50"} overflow-auto`}
    >
      {children}
    </div>
  );
};

export const Panes = ({ children }) => {
  return <div className="flex h-screen">{children}</div>;
};
