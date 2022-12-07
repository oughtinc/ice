import type { Meta, StoryObj } from "@storybook/react";

import { CallIconButton } from "./CallIconButton";

const meta: Meta<typeof CallIconButton> = {
  title: "TracePage/CallIconButton",
  component: CallIconButton,
};

export default meta;
type Story = StoryObj<typeof CallIconButton>;

export const Collapsed: Story = {
  args: {
    expanded: false,
    childCount: 3,
  },
};

export const Expanded: Story = {
  args: {
    expanded: true,
    childCount: 3,
  },
};

export const ModelCall: Story = {
  args: {
    isModelCall: true,
  },
};

export const NoChildren: Story = {
  args: {
    childCount: 0,
  },
};
