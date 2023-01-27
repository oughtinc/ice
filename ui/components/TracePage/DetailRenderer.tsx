import { useToast, UseToastOptions } from "@chakra-ui/react";
import { getFormattedName } from "/components/TracePage/CallName";
import {
  FlattenedFStringPart,
  flattenFString,
  FString,
  RawFStringPart,
} from "/components/TracePage/FString";
import classNames from "classnames";
import { useMemo, useState } from "react";
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

interface ArrayRendererProps {
  values: unknown[];
  shouldLogView: boolean;
}

function ArrayRenderer(props: ArrayRendererProps) {
  const [expanded, setExpanded] = useState(props.values.map(() => true));

  // if (props.shouldLogView) console.log('ArrayRenderer', props.values)
  return (
    <div>
      {props.values.map((el, index) => (
        <div key={index} className="mb-1">
          <span className="text-gray-600">{`${index + 1}. `}</span>
          {TypeIdentifiers[getStructuralType(el)]}
          {isCollapsible(el) ? (
            <ClickableDownArrow
              handleClick={() => {
                const newExpanded = expanded.slice();
                newExpanded[index] = !newExpanded[index];
                setExpanded(newExpanded);
              }}
            />
          ) : null}
          {expanded[index] ? <DetailRenderer data={el} /> : null}
        </div>
      ))}
    </div>
  );
}

interface ClickableDownArrowProps {
  handleClick: () => void;
}

function ClickableDownArrow(props: ClickableDownArrowProps) {
  return (
    <button onClick={props.handleClick}>
      <CaretDown />
    </button>
  );
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

interface ObjectRendererProps {
  values: [string, unknown][];
  shouldLogView: boolean;
}

interface IsExpandedMap {
  [key: string]: boolean;
}

function ObjectRenderer(props: ObjectRendererProps) {
  const allExpanded = props.values.reduce((acc, [key, _]) => {
    acc[key] = true;
    return acc;
  }, {} as IsExpandedMap);
  const [isExpanded, setIsExpanded] = useState(allExpanded);

  if (Object.keys(isExpanded).length !== props.values.length) {
    console.log("old isExpanded", isExpanded);
    console.log("new isExpanded", allExpanded);
    // setIsExpanded(allExpanded);
  }

  if (props.shouldLogView) console.log("ObjRenderer", props.values);
  return (
    <div>
      {props.values.map(function ([key, value], index) {
        if (props.shouldLogView) console.log("kv", key, value);
        return (
          <div key={index} className="mb-1">
            <span className="text-gray-600">{`${getFormattedName(key)}: `}</span>
            {TypeIdentifiers[getStructuralType(value)]}
            {isCollapsible(value) ? (
              <ClickableDownArrow
                handleClick={() => {
                  const newExpanded = { ...isExpanded };
                  newExpanded[key] = !newExpanded[key];
                  setIsExpanded(newExpanded);
                }}
              />
            ) : null}
            {isExpanded[key] ? <DetailRenderer data={value} /> : null}
          </div>
        );
      })}
    </div>
  );
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

function renderForArrayOrObject(view: ArrayView | ObjectView, root?: boolean) {
  return (
    <div className={classNames("flex", root ? undefined : "ml-4")}>
      <div>
        {view.type === "array" ? (
          <ArrayRenderer values={view.values} shouldLogView={false} />
        ) : (
          <ObjectRenderer values={view.values} shouldLogView={false} />
        )}

        {view.values.length === 0 ? <span className="text-gray-600">Empty</span> : null}
      </div>
    </div>
  );
}

function TestToSeeIfThingsBreak({ index, el }: { index: number; el: unknown }) {
  return (
    <div key={index} className="mb-1">
      <span className="text-gray-600">{`${index + 1}. `}</span>
      {TypeIdentifiers[getStructuralType(el)]}
      <DetailRenderer data={el} />
    </div>
  );
}

function XYZ({ view, root }: { view: ArrayView | ObjectView; root?: boolean }) {
  // notes: this works fine without usestate; confirming it fails w/ it
  // (and only on input???)
  // is the issue the conditional?

  let keys = [];
  if (view.type === "object") {
    keys.push(...view.values.map(([key, _]) => key));
  } else {
    keys.push(...view.values.map((_, index) => index + 1));
  }
  const allExpanded = keys.reduce((acc, key) => {
    acc[key] = true;
    return acc;
  }, {} as IsExpandedMap);

  // TODO oh lol...  (some lines are from copilot)
  // the bug: the state is not being updated when the component is re-rendered
  // the fix: use a reducer instead of useState
  // the reason: useState is not a reducer, so it doesn't update the state when the component is re-rendered
  // bug is that isExpanded doesn't contain the right keys the first time
  // around, but it does after clicking 'source'

  const [isExpanded, setIsExpanded] = useState(allExpanded);
  console.log("isExpanded", isExpanded);

  if (view.type === "object") {
    if (Object.keys(isExpanded).length !== view.values.length) {
      setIsExpanded(allExpanded);
    }
  }

  return (
    <div className={classNames("flex", root ? undefined : "ml-4")}>
      <div>
        {view.type === "array"
          ? view.values.map((el, index) => <TestToSeeIfThingsBreak index={index} el={el} />)
          : view.values.map(function ([key, value], index) {
              return (
                <div key={index} className="mb-1">
                  <span className="text-gray-600">{`${getFormattedName(key)}: `}</span>
                  {TypeIdentifiers[getStructuralType(value)]}
                  {isCollapsible(value) ? (
                    <ClickableDownArrow
                      handleClick={() => {
                        console.log("click me pl0x");
                      }}
                    />
                  ) : null}
                  {isExpanded[key] ? <DetailRenderer data={value} /> : null}
                </div>
              );
            })}
        {view.values.length === 0 ? <span className="text-gray-600">Empty</span> : null}
      </div>
    </div>
  );
}

function renderForValue(view: ValueView, toast: (x: UseToastOptions | undefined) => void) {
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
  const toast = useToast();
  /*const view: JsonChild = useMemo(() => {
    if (typeof data === "object" && data) {
      return buildViewForArrayOrObject(data);
    }
    return { type: "value", value: data };
  }, [data]);*/

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
    return renderForArrayOrObject(view, root);
  }
  return renderForValue(view, toast);
};

export const MetailRenderer = ({
  data,
  root,
  shouldLogView,
}: {
  data: unknown;
  root?: boolean;
  shouldLogView: boolean;
}) => {
  const toast = useToast();
  const view: JsonChild = // useMemo(() => {
    (function () {
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
    })();

  if (shouldLogView) {
    console.log("view", view);
  }
  if (view.type === "array" || view.type === "object") {
    return <XYZ view={view} root={root} />;
    /*return (
      <div className={classNames("flex", root ? undefined : "ml-4")}>
        <div>
          {view.type === "array"
            ? view.values.map((el, index) => (
              <TestToSeeIfThingsBreak index={index} el={el} />
            ))
            :
            view.values.map(([key, value], index) => (
              <div key={index} className="mb-1">
                <span className="text-gray-600">{`${getFormattedName(key)}: `}</span>
                {TypeIdentifiers[getStructuralType(value)]}
                <DetailRenderer data={value} shouldLogView={false} />
              </div>
            ))}
          {view.values.length === 0 ? <span className="text-gray-600">Empty</span> : null}
        </div>
      </div>
    );*/
    /*return (
      <div className={classNames("flex", root ? undefined : "ml-4")}>
        <div>
          {view.type === "array" ? (
            <ArrayRenderer shouldLogView={shouldLogView} values={view.values} />
          ) : (
            <ObjectRenderer values={view.values} shouldLogView={shouldLogView} />
          )}

          {view.values.length === 0 ? <span className="text-gray-600">Empty</span> : null}
        </div>
      </div>
    );*/
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
