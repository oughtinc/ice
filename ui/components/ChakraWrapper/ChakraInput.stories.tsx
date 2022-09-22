import { Input, InputGroup, InputLeftElement } from "@chakra-ui/react";
import { MagnifyingGlass } from "phosphor-react";
import { Fragment } from "react";

const story = { component: Input };
export default story;

const VARIANTS = ["outline"] as const;
const COLOR_SCHEMES = ["slate"] as const;
const STATES = ["empty", "with-input", "empty + with-icon", "with-input + with-icon"] as const;

export const Default = () => (
  <>
    {VARIANTS.map(variant => (
      <Fragment key={variant}>
        <div className="capitalize mb-2 mt-4">{variant}</div>
        <div className="grid grid-cols-4 gap-2">
          {COLOR_SCHEMES.flatMap(colorScheme =>
            STATES.map(state => {
              const key = `${colorScheme}-${state}`;
              const inputElement = (
                <Input
                  key={key}
                  variant={variant}
                  colorScheme={colorScheme}
                  placeholder="Some placeholder"
                  defaultValue={state.includes("with-input") ? "Some input" : undefined}
                  autoFocus={state.includes("focussed") ? true : undefined}
                />
              );
              return state.includes("with-icon") ? (
                <InputGroup key={key}>
                  <InputLeftElement className="text-slate-400">
                    <MagnifyingGlass className="ml-1" size={16} />
                  </InputLeftElement>
                  {inputElement}
                </InputGroup>
              ) : (
                inputElement
              );
            }),
          )}
        </div>
      </Fragment>
    ))}
  </>
);
