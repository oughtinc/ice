import { AgGridReact } from "ag-grid-react";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";
import { isEmpty, uniq } from "lodash";
import { Fragment } from "react";
import { Alert } from "@chakra-ui/react";

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
  const noRows = !rows.length;
  const noColumns = rows.every(isEmpty);
  return noRows || noColumns ? (
    <Alert className="m-4 w-fit">
      {noRows ? "No function is selected" : "The selected function has no columns"}
    </Alert>
  ) : (
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
