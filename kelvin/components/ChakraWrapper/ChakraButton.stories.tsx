import { Button } from "@chakra-ui/react";
import classNames from "classnames";
import { CloudArrowUp, MagnifyingGlass } from "phosphor-react";
import { Fragment } from "react";
import { IconButton } from "./IconButton";

const story = { component: Button };
export default story;

const VARIANTS = ["solid", "rounded", "outline", "ghost"] as const;
const STATES = ["default", "hover", "focus", "active", "disabled"] as const;
const SIZES = ["xs", "sm", "md", "lg"] as const;

const makeId = ({
  variant,
  size,
  state,
  type,
}: {
  variant: string;
  size: string;
  state: string;
  type: "icon" | "text";
}) => `${variant}-${state}-${size}-${type}`;

export const Default = () => (
  <table className="border-separate border-spacing-2">
    <tr>
      <td />
      <td />
      {[...SIZES, ...SIZES].map((size, i) => (
        <td key={i} className="text-base font-semibold text-slate-500 align-top text-center">
          {size}
        </td>
      ))}
    </tr>
    {VARIANTS.map((variant, variantIndex) => (
      <Fragment key={variant}>
        {variantIndex !== 0 && <tr className="h-8" />}
        {STATES.map((state, stateIndex) => (
          <tr key={`${variant}--${state}`} className={classNames(stateIndex === 0 && "mt-6")}>
            {stateIndex === 0 && (
              <td
                className="capitalize text-2xl font-semibold text-slate-700 align-top"
                rowSpan={STATES.length}
              >
                {variant}
              </td>
            )}
            <td className="capitalize text-base font-semibold text-slate-500 align-top">{state}</td>
            {SIZES.map(size => (
              <td key={`text-${size}`} className="align-top">
                <Button
                  variant={variant}
                  size={size}
                  id={makeId({ variant, size, state, type: "text" })}
                  colorScheme={["solid", "rounded"].includes(variant) ? "blue" : "gray"}
                  disabled={state === "disabled"}
                  isActive={state === "active"}
                  leftIcon={<MagnifyingGlass />}
                  rightIcon={<CloudArrowUp />}
                >
                  Button
                </Button>
              </td>
            ))}
            {SIZES.map(size => (
              <td key={`icon-${size}`} className="align-top">
                <IconButton
                  variant={variant}
                  size={size}
                  id={makeId({ variant, size, state, type: "icon" })}
                  colorScheme={["solid", "rounded"].includes(variant) ? "blue" : "gray"}
                  disabled={state === "disabled"}
                  isActive={state === "active"}
                  aria-label=""
                >
                  <CloudArrowUp />
                </IconButton>
              </td>
            ))}
          </tr>
        ))}
      </Fragment>
    ))}
  </table>
);
const ALL_COMBINATIONS = VARIANTS.flatMap(variant =>
  STATES.flatMap(state =>
    SIZES.flatMap(size =>
      (["text", "icon"] as const).map(type => ({ variant, state, size, type })),
    ),
  ),
);
Default.parameters = {
  pseudo: {
    hover: ALL_COMBINATIONS.filter(({ state }) => state === "hover").map(
      combination => `#${makeId(combination)}`,
    ),
    focus: ALL_COMBINATIONS.filter(({ state }) => state === "focus").map(
      combination => `#${makeId(combination)}`,
    ),
  },
};
