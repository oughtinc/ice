import classNames from "classnames";
import { upperFirst } from "lodash";

export const getFormattedName = (snakeCasedName: string) => {
  const spacedName = snakeCasedName.replace(/_/g, " ");
  return upperFirst(spacedName);
};

export interface CallFunction {
  name: string; // function name
  cls?: string; // class name for methods
}

export const CallName = ({ className, name, cls }: CallFunction & { className?: string }) => {
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
