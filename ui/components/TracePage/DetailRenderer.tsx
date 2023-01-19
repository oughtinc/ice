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
import { CaretDown } from "phosphor-react";

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

interface ArrayRendererState {
  expanded: boolean[];
}

class ArrayRenderer extends Component<Props, ArrayRendererState> {
  constructor(props: Props) {
    super(props);
    this.state = {
      expanded: this.props.values.map(() => true),
    } as ArrayRendererState;
  }

  override render() {
    return this.props.values.map((el, index) => (
      <div key={index} className="mb-1">
        <span className="text-gray-600">{`${index + 1}. `}</span>
        {TypeIdentifiers[getStructuralType(el)]}
        {isCollapsible(el) ? (
          <ClickableDownArrow
            handleClick={() => {
              this.setState(state => {
                const expanded = state.expanded.slice();
                expanded[index] = !expanded[index];
                return { expanded };
              });
            }}
          />
        ) : null}
        {this.state.expanded[index] ? <DetailRenderer data={el} /> : null}
      </div>
    ));
  }
}

interface Propz {
  values: [string, unknown][];
}

interface ClickyProps {
  handleClick: () => void;
}

class ClickableDownArrow extends Component<ClickyProps> {
  override render() {
    return (
      <button>
        <CaretDown onClick={this.props.handleClick} />
      </button>
    );
  }
}

interface IsExpandedMap {
  [key: string]: boolean;
}

interface ObjectRendererState {
  isExpanded: IsExpandedMap;
}

function isCollapsible(value: unknown): boolean {
  const structuralType = getStructuralType(value);
  if (structuralType === "value") return false;
  // empty arrays are ok
  if (structuralType === "array") return true;
  if (structuralType === "object") {
    // empty objects are ok
    // TODO someday use something like existential types to clean up this code
    const isFString = typeof value === "object" && value && "__fstring__" in value;
    return !isFString;
  }
  return false;
}

// TODO review all
class ObjectRenderer extends Component<Propz, ObjectRendererState> {
  constructor(props: Propz) {
    super(props);
    const allExpanded = props.values.reduce((acc, [key, _]) => {
      acc[key] = true;
      return acc;
    }, {} as IsExpandedMap);
    this.state = {
      isExpanded: allExpanded,
    };
  }

  override render() {
    return this.props.values.map(([key, value], index) => (
      <div key={index} className="mb-1">
        <span className="text-gray-600">{`${getFormattedName(key)}: `}</span>
        {TypeIdentifiers[getStructuralType(value)]}
        {isCollapsible(value) ? (
          <ClickableDownArrow
            handleClick={() =>
              this.setState(() => {
                return {
                  isExpanded: { ...this.state.isExpanded, [key]: !this.state.isExpanded[key] },
                };
              })
            }
          />
        ) : null}
        {this.state.isExpanded[key] ? <DetailRenderer data={value} /> : null}
      </div>
    ));
  }
}

function buildViewForFString(data: { __fstring__: unknown }): JsonChild {
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

interface ArrayView {
  type: "array";
  values: unknown[];
}

interface ObjectView {
  type: "object";
  values: [string, unknown][];
}

interface ValueView {
  type: "value";
  value: unknown;
  fstring?: FlattenedFStringPart[];
}

type ArrayOrObjectView = ArrayView | ObjectView;

function renderForArrayOrObject(view: ArrayOrObjectView, root?: boolean) {
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

function renderForValue(view: ValueView) {
  const toast = useToast();
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
    }
    return { type: "value", value: data };
  }, [data]);

  if (view.type === "array" || view.type === "object") {
    return renderForArrayOrObject(view, root);
  }
  return renderForValue(view);
};
