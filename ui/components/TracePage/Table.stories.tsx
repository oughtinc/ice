import type { Meta, StoryObj } from "@storybook/react";

import { Table } from "./Table";

const meta: Meta<typeof Table> = {
  title: "TracePage/Table",
  component: Table,
  decorators: [
    Story => (
      <div style={{ height: "240px" }}>
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof Table>;

export const CarTable: Story = {
  args: {
    rows: [
      { make: "Toyota", model: "Celica", price: 35000 },
      { make: "Ford", model: "Mondeo", price: 32000 },
      { make: "Porsche", model: "Boxster", price: 72000 },
    ],
  },
};

export const TableWithNoColumns: Story = {
  args: {
    rows: [{}, {}, {}],
  },
};

export const TableWithNoRows: Story = {
  args: {
    rows: [],
  },
};
