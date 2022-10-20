import { Alert, AlertDescription, AlertIcon } from "@chakra-ui/react";
import { Fragment } from "react";

const story = { component: Alert };
export default story;

const VARIANTS = ["subtle"] as const;
const STATUSES = ["error", "info", "warning", "success"] as const;
const STATES = ["default", "long-message", "with-icon", "long-message + with-icon"] as const;

export const Default = () => (
  <>
    {VARIANTS.map(variant => (
      <Fragment key={variant}>
        <div className="capitalize mb-2 mt-4">{variant}</div>
        <div className="grid grid-cols-4 gap-2">
          {STATUSES.flatMap(status =>
            STATES.map(state => {
              const key = `${status}-${state}`;

              return (
                <Alert className="h-fit" variant="subtle" key={key} status={status}>
                  {state.includes("with-icon") && <AlertIcon />}
                  <AlertDescription>
                    {state.includes("long-message")
                      ? "Some multi line long error message part 1. Some multi line long error message part 2"
                      : "Some error message"}
                  </AlertDescription>
                </Alert>
              );
            }),
          )}
        </div>
      </Fragment>
    ))}
  </>
);
