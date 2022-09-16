import { Button } from "@chakra-ui/react";
import { Fragment } from "react";

const story = { component: Button };
export default story;

const VARIANTS = ["customVariant", "outlined", "ghost", "lightGhost"] as const;
const COLOR_SCHEMES = ["blue", "red", "blueGray"] as const;
const STATES = ["normal", "normal + hover", "active", "active + hover"] as const;

const makeId = ({
  variant,
  colorScheme,
  state,
}: {
  variant: string;
  colorScheme: string;
  state: string;
}) => `${variant}-${colorScheme}-${state}`;

export const Default = () => (
  <>
    {VARIANTS.map(variant => (
      <Fragment key={variant}>
        <div className="capitalize mb-2 mt-4">{variant}</div>
        <div className="grid grid-cols-4 gap-2">
          {COLOR_SCHEMES.flatMap(colorScheme =>
            STATES.map(state => (
              <Button
                key={`${colorScheme}-${state}`}
                id={makeId({ variant, colorScheme, state })}
                variant={variant}
                colorScheme={colorScheme}
                isActive={state.includes("active")}
              >
                {state}
              </Button>
            )),
          )}
        </div>
      </Fragment>
    ))}
  </>
);
Default.parameters = {
  pseudo: {
    hover: VARIANTS.flatMap(variant =>
      COLOR_SCHEMES.flatMap(colorScheme =>
        STATES.filter(state => state.includes("hover")).map(
          state => `#${makeId({ variant, colorScheme, state })}`,
        ),
      ),
    ),
  },
};
