const StatusBar = ({ loading, error }: { loading: boolean; error: Error }) => {
  let message, color, icon;
  if (loading) {
    message = "Loading...";
    color = "text-gray-500";
    icon = <svg className="w-4 h-4 animate-spin mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v3m0 6v3m-6-3h3m6 0h3m-9-9l3 3m0 6l-3 3" />
    </svg>;
  } else if (error) {
    message = `Error: ${error.message}`;
    color = "text-red-500";
    icon = <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>;
  } else {
    message = "Ready";
    color = "text-green-500";
    icon = <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>;
  }
  return (
      <div className={`fixed bottom-0 left-0 right-0 h-10 px-4 py-2 flex items-center ${color} bg-gray-100`}
          aria-live="polite"
      >
          {icon} {message}
      </div>
  );
};

export default StatusBar;
