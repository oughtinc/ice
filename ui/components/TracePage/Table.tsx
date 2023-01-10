import { AgGridReact } from "ag-grid-react";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";
import { uniq } from "lodash";
import { Fragment } from "react";

export type StringToScalar = Record<string, boolean | number | string | null>;

export const Table = ({
  rows,
  rowIds = [],
  onFocusChange,
}: {
  rows: StringToScalar[];
  rowIds?: string[];
  onFocusChange?: (rowId?: string) => void;
}) => {
  const pagination = rows.length > 100;
  return (
    // AgGridReact doesn't respect changes to 'pagination' while the component is mounted.
    <Fragment key={String(pagination)}>
      <AgGridReact<StringToScalar>
        className="ag-theme-alpine w-full h-full"
        columnDefs={uniq(rows.flatMap(Object.keys)).map(field => ({ field }))}
        defaultColDef={{ filter: true, sortable: true, resizable: true }}
        onCellFocused={({ rowIndex }) =>
          onFocusChange?.(rowIndex === null ? undefined : rowIds?.[rowIndex])
        }
        pagination={pagination}
        rowData={rows}
      ></AgGridReact>
    </Fragment>
  );
};
