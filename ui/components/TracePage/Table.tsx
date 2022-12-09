import { AgGridReact } from "ag-grid-react";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";
import { uniq } from "lodash";

export type StringToScalar = Record<string, boolean | number | string | null>;

export const Table = ({ rows }: { rows: StringToScalar[] }) => (
  <AgGridReact<StringToScalar>
    className="ag-theme-alpine w-full"
    domLayout="autoHeight"
    defaultColDef={{ filter: true, sortable: true, resizable: true }}
    columnDefs={uniq(rows.flatMap(Object.keys)).map(field => ({ field }))}
    rowData={rows}
  ></AgGridReact>
);
