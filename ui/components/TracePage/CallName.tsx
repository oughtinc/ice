import classNames from "classnames";

export const CallName = ({ className, name, cls }: CallNameProps) => {
  const displayName = (name === "execute" || name === "run") && cls ? cls : name;
  return (
    <div className="flex items-center gap-1">
      {cls && cls !== displayName ? (
        <span className={classNames(className, "text-gray-500")}>{getFormattedName(cls)}:</span>
      ) : undefined}
      <span className={className}>{getFormattedName(displayName)}</span>
    </div>
  );
};

export interface CallFunction {
  name: string; // function name
  cls?: string; // class name for methods
}

interface CallNameProps extends CallFunction {
  className?: string;
}

export const getFormattedName = (snakeCasedName: string) => {
  const spacedName = snakeCasedName.replace(/_/g, " ");
  const capitalizedAndSpacedName = spacedName
    ? spacedName[0].toUpperCase() + spacedName.slice(1)
    : snakeCasedName;
  return capitalizedAndSpacedName;
};
