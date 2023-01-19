import type { Meta, StoryObj } from "@storybook/react";

import { DetailRenderer } from "./DetailRenderer";

const meta: Meta<typeof DetailRenderer> = {
  title: "TracePage/DetailRenderer",
  component: DetailRenderer,
};

// TODO surely we can automate all this jargon

export default meta;

type Story = StoryObj<typeof DetailRenderer>;

// TODO ensure that the fstrings in subparts are rendered with a test :)

// TODO how to set up a storybook test for this? such that the clicks are handled

export const Nested: Story = {
  args: {
    data: {
      foo: "bar",
      baz: {
        // TODO is this the expected behavior with nested fstrings?
        // TODO and them only being on one line?
        __fstring__: [
          "inner ",
          {
            __fstring__: ["inmost ", { source: "1", value: "1", formatted: "1" }],
          },
          { source: "2", value: "2", formatted: "2" },
        ],
      },
      qux: [1, 2, 3],
      oneElement: [1],
      duplicateName: [500],
      containingDuplicateName: {
        duplicateName: [501],
      },
      /*      fakeFString: {
              __fstring__: 100,
              barbarbar: 1e9
            }, */
    },
  },
};
