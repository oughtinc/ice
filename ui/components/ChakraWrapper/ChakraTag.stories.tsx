import { Tag, TagCloseButton, TagLabel } from "@chakra-ui/react";
import { Fragment } from "react";

const story = { component: Tag };
export default story;

const VARIANTS = ["subtle"] as const;
const COLOR_SCHEMES = ["blue", "rose", "slate"] as const;
const STATES = ["normal", "with-close"] as const;

export const Default = () => (
  <>
    {VARIANTS.map(variant => (
      <Fragment key={variant}>
        <div className="capitalize mb-2 mt-4">{variant}</div>
        <div className="grid grid-cols-4 gap-2">
          {COLOR_SCHEMES.flatMap(colorScheme =>
            STATES.map(state => (
              <Tag
                key={`${colorScheme}-${state}`}
                className="w-fit"
                variant={variant}
                colorScheme={colorScheme}
              >
                <TagLabel>Some Value</TagLabel>
                {state.includes("with-close") ? <TagCloseButton /> : null}
              </Tag>
            )),
          )}
        </div>
      </Fragment>
    ))}
  </>
);
