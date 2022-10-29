const Action = ({ kind, params, label }) => {
  return (
    <div className="action">
      <span className="action-label">{label}</span>
    </div>
  );
};

export default Action;
