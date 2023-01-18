import { Button, Collapse, Skeleton, useToast } from "@chakra-ui/react";
import { getFormattedName } from "/components/TracePage/CallName";
import {
  FlattenedFStringPart,
  flattenFString,
  FString,
  RawFStringPart,
} from "/components/TracePage/FString";
import classNames from "classnames";
import {
  Component,
  createContext,
  Dispatch,
  ReactNode,
  SetStateAction,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

type JsonChild =
  | { type: "array"; values: unknown[] }
  | { type: "object"; values: [string, unknown][] }
  | { type: "value"; value: unknown; fstring?: FlattenedFStringPart[] };

const getStructuralType = (data: unknown) => {
  if (typeof data === "object" && data && !Array.isArray(data)) return "object";
  if (Array.isArray(data)) return "array";
  return "value";
};

const TypeIdentifiers = {
  object: <span className="shrink-0 font-mono mr-[8px]">{"{}"}</span>,
  array: <span className="shrink-0 font-mono mr-[8px]">{"[]"}</span>,
  value: null,
};

interface Props {
  //    view: { type: "array"; values: unknown[] };
  //    view: JsonChild
  values: unknown[];
}

class ArrayRenderer extends Component<Props, number> {
  override render() {
    return this.props.values.map((el, index) => (
      <div key={index} className="mb-1">
        <span className="text-gray-600">{`${index + 1}. `}</span>
        {TypeIdentifiers[getStructuralType(el)]}
        <DetailRenderer data={el} />
      </div>
    ));
  }
}
interface Propz {
  //    view: { type: "array"; values: unknown[] };
  //    view: JsonChild
  values: [string, unknown][];
}

class ObjectRenderer extends Component<Propz, number> {
  override render() {
    return this.props.values.map(([key, value], index) => (
      <div key={index} className="mb-1">
        <span className="text-gray-600">{`${getFormattedName(key)}: `}</span>
        {TypeIdentifiers[getStructuralType(value)]}
        <DetailRenderer data={value} />
      </div>
    ));
  }
}

export const DetailRenderer = ({ data, root }: { data: unknown; root?: boolean }) => {
  const toast = useToast();
  const view: JsonChild = useMemo(() => {
    if (typeof data === "object" && data) {
      // Array or Object
      if (Array.isArray(data)) return { type: "array", values: data };
      if ("__fstring__" in data) {
        const parts = data.__fstring__ as RawFStringPart[];
        const flattenedParts = flattenFString(parts);
        const value = flattenedParts
          .map(part => (typeof part === "string" ? part : part.value))
          .join("");
        return { type: "value", value, fstring: flattenedParts };
      }
      return { type: "object", values: Object.entries(data) };
    }
    return { type: "value", value: data };
  }, [data]);

  if (view.type === "array" || view.type === "object") {
    return (
      <div className={classNames("flex", root ? undefined : "ml-4")}>
        <div>
          {view.type === "array" ? (
            <ArrayRenderer values={view.values} />
          ) : (
            <ObjectRenderer values={view.values} />
          )}

          {view.values.length === 0 ? <span className="text-gray-600">Empty</span> : null}
        </div>
      </div>
    );
  }
  const value = `${view.value}`;
  return value ? (
    <span
      className="inline whitespace-pre-wrap"
      onClick={() => {
        navigator.clipboard.writeText(value);
        toast({ title: "Copied to clipboard", duration: 1000 });
      }}
    >
      {view.fstring ? <FString parts={view.fstring} /> : value}
    </span>
  ) : (
    <span className="text-gray-600">empty</span>
  );
};
