export const Pane = ({ children, active, status }) => {
  return (
    <div className="flex-1 border flex flex-col">
      <div className={`flex-1 ${active ? "opacity-100" : "bg-gray-100 opacity-50"} overflow-auto`}>
        {children}
      </div>
      <div
        className={`sticky bottom-0 left-0 right-0 h-6 bg-gray-200 text-gray-600 text-sm flex items-center justify-center ${
          active ? "opacity-100" : "opacity-50"
        }`}
      >
        {status}
      </div>
    </div>
  );
};

export const Panes = ({ children }) => {
  return <div className="flex h-screen">{children}</div>;
};
