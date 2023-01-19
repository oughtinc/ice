import { useToast } from "@chakra-ui/react";
import { getFormattedName } from "/components/TracePage/CallName";
import {
  FlattenedFStringPart,
  flattenFString,
  FString,
  RawFStringPart,
} from "/components/TracePage/FString";
import classNames from "classnames";
import { Component, useMemo } from "react";

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

// TODO name maybe should be different
type FStringyData = {
  __fstring__: unknown;
};

function buildViewForFString(data: FStringyData): JsonChild {
  const parts = data.__fstring__ as RawFStringPart[];
  const flattenedParts = flattenFString(parts);
  const value = flattenedParts.map(part => (typeof part === "string" ? part : part.value)).join("");
  return { type: "value", value, fstring: flattenedParts };
}

function buildViewForArrayOrObject(data: object): JsonChild {
  if (Array.isArray(data)) return { type: "array", values: data };
  if ("__fstring__" in data) {
    return buildViewForFString(data);
  }
  return { type: "object", values: Object.entries(data) };
}

function renderForArrayOrObject(view: JsonChild, root?: boolean) {
  // TODO what's a more idiomatic way to handle this?
  if (view.type !== "array" && view.type !== "object") {
    throw new Error("renderForArrayOrObject called with non-array or non-object");
  }
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

function renderForValue(view: JsonChild) {
  const toast = useToast();
  if (view.type !== "value") {
    throw new Error("renderForValue called with non-value");
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
}

export const DetailRenderer = ({ data, root }: { data: unknown; root?: boolean }) => {
  const view: JsonChild = useMemo(() => {
    if (typeof data === "object" && data) {
      return buildViewForArrayOrObject(data);
    } // TODO methods and constructors?
    return { type: "value", value: data };
  }, [data]);

  if (view.type === "array" || view.type === "object") {
    return renderForArrayOrObject(view, root);
  }
  return renderForValue(view);
};
