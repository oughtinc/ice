import { AgGridReact } from "ag-grid-react";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";
import { uniq } from "lodash";

export type StringToScalar = Record<string, boolean | number | string | null>;

export const Table = ({
  rows,
  rowIds = [],
  onFocusChange,
}: {
  rows: StringToScalar[];
  rowIds?: string[];
  onFocusChange?: ({ rowId }: { rowId: string | undefined }) => void;
}) => (
  <AgGridReact<StringToScalar>
    className="ag-theme-alpine w-full h-full"
    columnDefs={uniq(rows.flatMap(Object.keys)).map(field => ({ field }))}
    defaultColDef={{ filter: true, sortable: true, resizable: true }}
    onCellFocused={({ rowIndex }) =>
      onFocusChange?.({ rowId: rowIndex === null ? undefined : rowIds?.[rowIndex] })
    }
    pagination={rows.length > 100}
    rowData={rows}
  ></AgGridReact>
);
