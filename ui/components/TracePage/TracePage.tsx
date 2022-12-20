import { Button, Collapse, Skeleton, useToast } from "@chakra-ui/react";
import { Allotment } from "allotment";
import "allotment/dist/style.css";
import classNames from "classnames";
import produce from "immer";
import { isEmpty, last, memoize, set } from "lodash";
import {
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
import { ArcherContainer, ArcherElement } from "react-archer";
import { ArcherContainerHandle } from "react-archer/lib/ArcherContainer/ArcherContainer.types";
import SyntaxHighlighter from "react-syntax-highlighter";
import Spinner from "./Spinner";
import { recipes } from "/helpers/recipes";
import * as COLORS from "/styles/colors.json";
import { useParams } from "react-router";
import { getHighlightedCalls, isHighlighted, Toolbar } from "/components/TracePage/Toolbar";
import { CallFunction, CallName, getFormattedName } from "/components/TracePage/CallName";
import { CallIconButton } from "./CallIconButton";
import {
  FlattenedFStringPart,
  flattenFString,
  FString,
  RawFStringPart,
} from "/components/TracePage/FString";
import { StringToScalar, Table } from "./Table";

const elicitStyle = {
  "hljs-keyword": { color: COLORS.indigo[600] }, // use primary color for keywords
  "hljs-operator": { color: COLORS.indigo[600] }, // use primary color for operators
  "hljs-number": { color: COLORS.lightBlue[600] }, // use secondary color for numbers
  "hljs-decorator": { color: COLORS.indigo[600] }, // use primary color for decorators
  "hljs-comment": { color: COLORS.green[700] }, // use a muted green for comments
  "hljs-string": { color: "rgb(153, 102, 51)" }, // use a muted orange for strings
  "hljs-built_in": { color: COLORS.lightBlue[600] }, // use secondary color for built-ins
  "hljs-class": { color: COLORS.lightBlue[600] }, // use secondary color for classes
  "hljs-module": { color: COLORS.lightBlue[600] }, // use secondary color for modules
  "hljs-punctuation": { color: "rgb(51, 102, 153)" }, // use a darker shade of the secondary color for punctuation
  "hljs-bracket": { color: "rgb(51, 102, 153)" }, // use a darker shade of the secondary color for brackets
  "hljs-plain": { color: "rgb(128, 128, 128)" }, // use a neutral gray for plain text
};

const getContentLength = async (url: string) => {
  const response = await fetch(url, { method: "HEAD" });
  const length = parseInt(response.headers.get("content-length") ?? "", 10);
  return isNaN(length) ? 0 : length;
};

// Detailed values of a function call to show in the sidebar.
type InputOutputContentProps = {
  // Call arguments, i.e. inputs
  args: BlockAddress<Record<string, unknown>>;
  // The full return value
  result?: BlockAddress<unknown>;
  // Arbitrary optional additional data
  records?: Record<string, BlockAddress<unknown>>;
};

export interface CallInfo extends InputOutputContentProps {
  id: string; // unique ID
  parent: string; // outer call ID
  start: number; // start time
  name: string; // function name
  cls?: string; // class name for methods
  shortArgs: string; // short representation of args
  shortResult?: string[]; // short representation of return value
  children?: Calls; // nested calls
  fields?: StringToScalar; // short arbitrary fields associated with the call
  func: BlockAddress<FuncBlock>; // long info about the function itself
  end?: number; // end time
  totalTokens?: number;
}

interface FuncBlock {
  doc: string;
  source?: string;
}

export type Calls = Record<string, CallInfo>;

// Mapping from block number (identifies the filename) to a list of lines.
// Each line is a JSON string.
type Blocks = Record<number, string[]>;

// Describes where to load a value of type T from Blocks.
// Represents [block number, line number].
type BlockAddress<T> = [number, number];

const MODEL_CALL_NAMES = [
  "relevance",
  "answer",
  "predict",
  "classify",
  "prompted_classify",
  "complete",
];

const TreeContext = createContext<{
  traceId: string;
  rootId: string;
  calls: Calls;
  getBlockValue: <T>(block: BlockAddress<T>) => T | undefined;
  selectedId: string | undefined;
  setSelectedId: Dispatch<SetStateAction<string | undefined>>;
  getExpanded: (id: string) => boolean;
  setExpanded: (id: string, expanded: boolean) => void;
  setExpandedById: Dispatch<SetStateAction<Record<string, boolean>>>;
  getFocussed: (id: string) => boolean;
  highlightedFunction: CallFunction | undefined;
  setHighlightedFunction: Dispatch<SetStateAction<CallFunction | undefined>>;
  othersHidden: boolean;
  setOthersHidden: Dispatch<SetStateAction<boolean>>;
  isVisible: (id: string) => boolean;
} | null>(null);

const applyUpdates = (calls: Calls, updates: Record<string, unknown>) =>
  Object.entries(updates).forEach(([path, value]) => {
    set(calls, path, value);

    const id = path.split(".")[0];
    calls[id].id = id;

    if (path.endsWith(".fields.davinci_equivalent_tokens")) {
      const tokens = Number(value);
      if (isNaN(tokens)) return;
      const callId = path.split(".")[0];
      let call = calls[callId];
      while (call) {
        call.totalTokens = (call.totalTokens ?? 0) + tokens;
        call = calls[call.parent];
      }
    }
  });

const urlPrefix = (traceId: string) => {
  const base = recipes[traceId] ? "https://oughtinc.github.io/static" : "/api";
  return `${base}/traces/${traceId}`;
};

const TreeProvider = ({ traceId, children }: { traceId: string; children: ReactNode }) => {
  const traceOffsetRef = useRef(0);
  const [calls, setCalls] = useState<Calls>({});
  const [blocks, setBlocks] = useState<Blocks>({});
  const [selectedId, setSelectedId] = useState<string>();
  const [rootId, setRootId] = useState<string>("");
  const [expandedById, setExpandedById] = useState<Record<string, boolean>>({});
  const [autoselected, setAutoselected] = useState(false);
  const [highlightedFunction, setHighlightedFunction] = useState<CallFunction>();
  const [othersHidden, setOthersHidden] = useState(false);

  useEffect(() => {
    if (!autoselected) {
      const firstRoot = Object.keys(calls[traceId]?.children ?? {})[0];
      if (firstRoot) {
        setRootId(firstRoot);
        setExpandedById(current => ({ ...current, [firstRoot]: true }));
        const firstChild = Object.keys(calls[firstRoot]?.children ?? {})[0];
        if (firstChild) {
          setSelectedId(firstChild);
          setAutoselected(true);
        }
      }
    }
  }, [autoselected, calls, traceId]);

  const isMounted = useRef(true);

  useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout>;

    const poll = async () => {
      let delay = 1_000;
      try {
        const url = `${urlPrefix(traceId)}/trace.jsonl`;
        const offset = traceOffsetRef.current;
        const contentLength = await getContentLength(url);
        if (offset >= contentLength) return;

        const initialOffset = 1e6;
        const subsequentOffset = 1e9;
        const limit = Math.min(
          offset + (offset === 0 ? initialOffset : subsequentOffset),
          contentLength,
        );
        if (limit < contentLength) delay = 50;

        const response = await fetch(url, {
          headers: { Range: `bytes=${offset}-${limit}` },
        });
        const { status } = response;
        if (status !== 206) throw new Error(`Unexpected status: ${status}`);
        const text = await response.text();
        if (!isMounted.current) return;

        const end = text.lastIndexOf("\n") + 1;
        traceOffsetRef.current += end;
        setCalls(calls =>
          produce(calls, draft => {
            text
              .slice(0, end)
              .split("\n")
              .forEach(line => line && applyUpdates(draft, JSON.parse(line)));
          }),
        );
      } catch (e) {
        console.warn("fetch failed", e);
      } finally {
        if (isMounted.current) {
          timeoutId = setTimeout(poll, delay);
        }
      }
    };

    poll();

    return () => {
      isMounted.current = false;
      clearTimeout(timeoutId);
    };
  }, [traceId]);

  const getFocussed = useMemo(() => {
    const selectedCall = selectedId !== undefined ? calls[selectedId] : undefined;
    if (!selectedCall || !selectedId) {
      return () => true;
    }
    // Subtree from the selected call
    const getFocussedIds = (nodeId: string): string[] => [
      nodeId,
      ...(nodeId === rootId ? [] : getFocussedIds(calls[nodeId]?.parent)),
    ];
    const getFocussedIdsChildren = (nodeId: string): string[] => [
      nodeId,
      ...Object.keys(calls[nodeId]?.children ?? {}).flatMap(getFocussedIdsChildren),
    ];
    const focussedIds = [...getFocussedIds(selectedId), ...getFocussedIdsChildren(selectedId)];
    return (id: string) => focussedIds.includes(id);
  }, [selectedId, calls, rootId]);

  // Placeholders for this render cycle to avoid fetching the same block multiple times.
  // This gets updated during rendering, which is why we don't use state.
  const blockRequests = useRef<Set<number>>(new Set());

  function getBlockValue<T>(blockAddress: BlockAddress<T>): T | undefined {
    const [blockNumber, blockLineno] = blockAddress;
    const block = blocks[blockNumber];
    if (block) {
      if (blockLineno < block.length) {
        return JSON.parse(block[blockLineno]);
      }
      return undefined; // wait for the other lines
    }

    if (blockRequests.current.has(blockNumber)) {
      // This block has already been requested.
      return undefined;
    }
    blockRequests.current.add(blockNumber);

    const url = `${urlPrefix(traceId)}/block_${blockNumber}.jsonl`;
    const fetchBlock = async (start: number) => {
      // Note that the 999999999 is needed because our get_file implementation
      // requires both ends of the range to be specified.
      const response = await fetch(url, { headers: { Range: `bytes=${start}-999999999` } });
      const text = await response.text();

      if (!isMounted.current) return;

      start += text.length;
      const lines = text.split("\n");
      // Remove the last line. Normally it's empty, i.e. text should end in a newline.
      // This also handles lines being incomplete,
      // in which case `start` is moved to the beginning of that line.
      start -= lines.pop()!.length;

      if (last(lines) === "end") {
        lines.pop();
      } else {
        // This block is incomplete, schedule polling for the rest.
        setTimeout(() => fetchBlock(start), 1_000);
      }

      if (lines.length) {
        setBlocks((blocks: Blocks) => ({
          ...blocks,
          [blockNumber]: [...(blocks[blockNumber] ?? []), ...lines],
        }));
      }
    };
    fetchBlock(0);
    return undefined;
  }

  const isVisible = useMemo(() => {
    if (!othersHidden || !highlightedFunction) return () => true;

    const checkParents = memoize((id: string): boolean => {
      const call = calls[id];
      return call && (isHighlighted(call, highlightedFunction) || checkParents(call.parent));
    });
    const checkChildren = memoize((id: string): boolean => {
      const call = calls[id];
      return (
        call &&
        (isHighlighted(call, highlightedFunction) ||
          Object.keys(call.children || {}).some(checkChildren))
      );
    });
    return (id: string) => checkParents(id) || checkChildren(id);
  }, [othersHidden, highlightedFunction, calls]);

  return (
    <TreeContext.Provider
      value={{
        traceId,
        calls,
        getBlockValue,
        rootId,
        selectedId,
        setSelectedId,
        getExpanded: (id: string) => expandedById[id] ?? false,
        setExpanded: (id: string, expanded: boolean) => {
          if (id !== rootId) setExpandedById(current => ({ ...current, [id]: expanded }));
        },
        setExpandedById,
        highlightedFunction,
        setHighlightedFunction,
        getFocussed,
        othersHidden,
        setOthersHidden,
        isVisible,
      }}
    >
      {children}
    </TreeContext.Provider>
  );
};

export const useTreeContext = () => {
  const context = useContext(TreeContext);
  if (!context) throw new Error("useTreeContext must be used within a TreeProvider");
  return context;
};

const useCallInfo = (id: string) => {
  const { calls, selectedId, setSelectedId, getFocussed } = useTreeContext();
  return {
    ...calls[id],
    selected: selectedId === id,
    focussed: getFocussed(id),
    select: () => setSelectedId(id),
  };
};

const useSelectedCallInfo = (): CallInfo | undefined => {
  const { calls, selectedId } = useTreeContext();
  return selectedId ? calls[selectedId] : undefined;
};

const useExpanded = (id: string) => {
  const { getExpanded, setExpanded } = useTreeContext();
  return {
    expanded: getExpanded(id),
    setExpanded: (expanded: boolean) => setExpanded(id, expanded),
  };
};

const useLinks = () => {
  const { traceId, calls } = useTreeContext();

  const getParent = (id: string) => {
    const { parent } = calls[id];
    return parent !== traceId ? parent : undefined;
  };

  const getChildren = (id: string) => {
    const { children = {} } = calls[id] ?? {};
    return Object.keys(children);
  };

  const getSiblingAt = (offset: number) => (id: string) => {
    const siblings = getChildren(calls[id].parent);
    const index = siblings.indexOf(id);
    return siblings[index + offset];
  };

  return { getParent, getChildren, getPrior: getSiblingAt(-1), getNext: getSiblingAt(1) };
};

const isModelCall = ({ cls, name }: CallInfo) =>
  MODEL_CALL_NAMES.includes(name) && !!cls?.includes("Agent");

function lineAnchorId(id: string) {
  return `line-anchor-${id}`;
}

const COST_USD_PER_DAVINCI_TOKEN = 0.02 / 1000;
const CURRENCY_FORMATTER = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});

const Call = ({ id, refreshArcherArrows }: { id: string; refreshArcherArrows: () => void }) => {
  const callInfo = useCallInfo(id);
  const { selectedId, highlightedFunction, isVisible } = useTreeContext();
  const { getParent } = useLinks();
  const { expanded, setExpanded } = useExpanded(id);

  if (!isVisible(id)) return null;

  const {
    children = {},
    select,
    selected,
    focussed,
    shortArgs,
    shortResult,
    totalTokens,
    cls,
    name,
  } = callInfo;

  const childIds = Object.keys(children);
  const cost = totalTokens && totalTokens * COST_USD_PER_DAVINCI_TOKEN;

  const modelCall = isModelCall(callInfo);
  const isSiblingWithSelected = selectedId && getParent(id) === getParent(selectedId);

  return (
    <div className="mt-2 flex-shrink-0">
      <div
        className={classNames("flex flex-shrink-0 transition-opacity", {
          // Not focused but is sibling with selected node has a higher opacity
          // This assumes all calls are parallel; for sequential calls, we should
          // make previous call siblings more visible than later siblings.
          "opacity-30": !focussed && !isSiblingWithSelected,
          "opacity-60": !focussed && isSiblingWithSelected,
        })}
      >
        <Button
          as="div"
          className={classNames(
            "justify-start text-start items-start h-fit min-w-[300px] p-1.5 !shadow-none",
          )}
          variant="ghost"
          onClick={ev => {
            select();
            ev.stopPropagation();
          }}
          isActive={selected}
          {...(isHighlighted(callInfo, highlightedFunction)
            ? {
                borderColor: "yellow.500",
                borderWidth: "5px",
              }
            : {})}
        >
          <ArcherElement
            id={lineAnchorId(id)}
            relations={
              expanded
                ? childIds.map(childId => ({
                    targetId: lineAnchorId(childId),
                    targetAnchor: "left",
                    sourceAnchor: "bottom",
                  }))
                : []
            }
          >
            <CallIconButton
              expanded={expanded}
              onChange={expanded => {
                setExpanded(!expanded);
                // Theres a hard to debug layout thing here, where sometimes
                // the arrows don't redraw properly when nodes are expanded.
                setTimeout(() => refreshArcherArrows(), 50);
              }}
              childCount={childIds.length}
              isModelCall={modelCall}
            />
          </ArcherElement>
          <div className="mx-2">
            <CallName className="text-base text-slate-700" cls={cls} name={name} />
            <div className="text-sm text-gray-600 flex items-center">
              <span className="text-indigo-600">{shortArgs}</span>
              <span className="px-2">→</span>
              {shortResult === undefined ? (
                <Spinner size="small" />
              ) : (
                <ResultComponent value={shortResult} />
              )}
            </div>
          </div>
        </Button>
      </div>
      {!modelCall && (
        <Collapse in={expanded} transition={{ enter: { duration: 0 } }}>
          <div className="ml-12">
            {expanded && <CallChildren id={id} refreshArcherArrows={refreshArcherArrows} />}
          </div>
        </Collapse>
      )}
    </div>
  );
};

const CallChildren = ({
  id,
  refreshArcherArrows,
}: {
  id: string;
  refreshArcherArrows: () => void;
}) => {
  const { children = {} } = useCallInfo(id) ?? {};
  const childIds = Object.keys(children);

  return (
    <div className="flex flex-col">
      {childIds.map(id => (
        <Call key={id} id={id} refreshArcherArrows={refreshArcherArrows} />
      ))}
    </div>
  );
};

const ResultComponent = ({ value }: { value: string[] }): JSX.Element => {
  return (
    <>
      {value.map((string, idx) => (
        <div
          className="px-[4px] py-[2px] mx-[3px] bg-lightBlue-50 text-lightBlue-600 rounded-4"
          key={idx}
        >
          {string}
        </div>
      ))}
    </>
  );
};

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

const DetailRenderer = ({ data, root }: { data: unknown; root?: boolean }) => {
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
          {view.type === "array"
            ? view.values.map((el, index) => (
                <div key={index} className="mb-1">
                  <span className="text-gray-600">{`${index + 1}. `}</span>
                  {TypeIdentifiers[getStructuralType(el)]}
                  <DetailRenderer data={el} />
                </div>
              ))
            : view.values.map(([key, value], index) => (
                <div key={index} className="mb-1">
                  <span className="text-gray-600">{`${getFormattedName(key)}: `}</span>
                  {TypeIdentifiers[getStructuralType(value)]}
                  <DetailRenderer data={value} />
                </div>
              ))}
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

const Json = ({ name, value }: { name: string; value: unknown }) => {
  return (
    <div>
      <div className="mb-2 font-medium">{name}</div>
      {value === undefined ? (
        <Skeleton className="mt-4 h-4" />
      ) : (
        <DetailRenderer data={value} root />
      )}
    </div>
  );
};

const DetailPane = () => {
  const info = useSelectedCallInfo();
  if (!info) return null;
  return <DetailPaneContent info={info} />;
};

type DetailPaneContentProps = {
  info: CallInfo;
};

type Tab = "io" | "src";

const DetailPaneContent = ({ info }: DetailPaneContentProps) => {
  const { func, cls, name } = info;
  const [tab, setTab] = useState<Tab>("io"); // io for inputs and outputs, src for source
  const { getBlockValue } = useTreeContext();

  return (
    <div className="flex-1 p-6">
      <TabHeader cls={cls} name={name} doc={getBlockValue(func)?.doc} />
      <TabBar tab={tab} setTab={setTab} />
      <TabContent tab={tab} info={info} />
    </div>
  );
};

const TabHeader = ({ cls, name, doc }: { cls?: string; name: string; doc?: string }) => (
  <div className="mb-4">
    <h3 className="text-lg font-semibold text-gray-800">
      <CallName cls={cls} name={name} />
    </h3>
    <p className="text-gray-600 text-sm whitespace-pre-line">{doc}</p>
  </div>
);

const TabBar = ({ tab, setTab }: { tab: Tab; setTab: (tab: Tab) => void }) => (
  <div className="flex justify-between items-center border-b border-gray-200">
    <div className="space-x-4">
      <TabButton label="Inputs and Outputs" value="io" tab={tab} setTab={setTab} />
      <TabButton label="Source" value="src" tab={tab} setTab={setTab} />
    </div>
  </div>
);

type TabButtonProps = {
  label: string;
  value: Tab;
  tab: Tab;
  setTab: (tab: Tab) => void;
};

const TabButton = ({ label, value, tab, setTab }: TabButtonProps) => (
  <button
    className={`py-2 px-4 ${
      tab === value
        ? "text-blue-600 border-b-2 border-blue-600"
        : "text-gray-600 hover:text-blue-600"
    }`}
    onClick={() => setTab(value)}
  >
    {label}
  </button>
);

const TabContent = ({ tab, info }: { tab: Tab; info: CallInfo }) => {
  const { func, args, records, result } = info;
  const { getBlockValue } = useTreeContext();

  return (
    <div className="space-y-4 mt-4">
      {tab === "io" ? (
        <InputOutputContent args={args} records={records} result={result} />
      ) : (
        <SourceContent source={getBlockValue(func)?.source} />
      )}
    </div>
  );
};

const excludeMetadata = (source: Record<string, unknown> | undefined) => {
  if (source === undefined) return undefined;
  return Object.fromEntries(
    Object.entries(source).filter(([key, value]) => !["self", "paper"].includes(key)),
  );
};

const InputOutputContent = ({ args, records, result }: InputOutputContentProps) => {
  const { getBlockValue } = useTreeContext();
  return (
    <>
      <Json name="Inputs" value={excludeMetadata(getBlockValue(args))} />
      {!isEmpty(records) && (
        <Json
          name="Records"
          value={Object.values(records)
            .map(getBlockValue)
            .filter(v => v)}
        />
      )}
      <Json name="Outputs" value={result && getBlockValue(result)} />
    </>
  );
};

type SourceContentProps = {
  source: string | undefined;
};

const SourceContent = ({ source }: SourceContentProps) => {
  if (!source) {
    return <p>Source code not available</p>;
  }
  const strippedSource = stripIndent(source);

  return (
    <SyntaxHighlighter
      language="python"
      className="bg-gray-100 p-4 rounded-md overflow-auto text-sm"
      style={elicitStyle}
      customStyle={{ backgroundColor: "transparent" }}
    >
      {strippedSource}
    </SyntaxHighlighter>
  );
};

type Bindings = Record<string, () => void>;

const withVimBindings = (bindings: Bindings): Bindings => ({
  ...bindings,
  h: bindings.ArrowLeft,
  j: bindings.ArrowDown,
  k: bindings.ArrowUp,
  l: bindings.ArrowRight,
});

const stripIndent = (source: string): string => {
  // Find the minimum number of leading spaces on any non-empty line
  const indent = source
    .split("\n")
    .filter((line: string) => line.trim()) // ignore empty lines
    .reduce(
      (min: number, line: string) => Math.min(min, line.match(/^\s*/)?.[0].length ?? 0),
      Infinity,
    );

  // Remove that many spaces from the start of each line
  return source
    .split("\n")
    .map((line: string) => line.slice(indent))
    .join("\n");
};

const Trace = ({ traceId }: { traceId: string }) => {
  const {
    calls,
    selectedId,
    rootId,
    setSelectedId,
    getExpanded,
    setExpanded,
    highlightedFunction,
  } = useTreeContext();
  const { getParent, getChildren, getPrior, getNext } = useLinks();
  // const params = useParams()

  const maybeSetSelectedId = useCallback(
    (update: (id: string) => string | undefined) => {
      setSelectedId(id => {
        const res = update(id as any) || id;
        return id && res;
      });
    },
    [setSelectedId],
  );

  const getExpandedChildren = useCallback(
    (id: string) => (getExpanded(id) ? getChildren(id) : []),
    [getChildren, getExpanded],
  );

  const nextFrom = useCallback(
    (id: string | undefined): string | undefined => id && (getNext(id) || nextFrom(getParent(id))),
    [getNext, getParent],
  );

  const bindings = useMemo(
    () =>
      (selectedId
        ? withVimBindings({
            ArrowUp: () =>
              maybeSetSelectedId(id => {
                let lastDescendantOfPrior = getPrior(id);
                if (!lastDescendantOfPrior) return getParent(id);

                for (;;) {
                  const lastChild = last(getExpandedChildren(lastDescendantOfPrior));
                  if (!lastChild) return lastDescendantOfPrior;
                  lastDescendantOfPrior = lastChild;
                }
              }),
            ArrowDown: () => {
              maybeSetSelectedId(id => getExpandedChildren(id)[0] || nextFrom(id));
            },
            ArrowLeft: () =>
              getExpandedChildren(selectedId).length
                ? setExpanded(selectedId, false)
                : maybeSetSelectedId(getParent),
            ArrowRight: () => getChildren(selectedId).length && setExpanded(selectedId, true),
            Escape: () => maybeSetSelectedId(_ => rootId),
          })
        : {}) as Bindings,
    [
      getChildren,
      getExpandedChildren,
      getParent,
      getPrior,
      maybeSetSelectedId,
      nextFrom,
      selectedId,
      setExpanded,
      rootId,
    ],
  );

  useEffect(() => {
    const keyListener = (event: KeyboardEvent) => {
      // Ignore events when the table is in focus.
      if (
        event.target instanceof Node &&
        document.querySelector(".call-table")?.contains(event.target)
      ) {
        return;
      }

      const binding = bindings[event.key];
      if (binding) {
        event.stopPropagation();
        event.preventDefault();
        binding();
      }
    };

    window.addEventListener("keydown", keyListener);
    return () => window.removeEventListener("keydown", keyListener);
  }, [bindings]);

  const firstRoot = getChildren(traceId)[0];

  const archerContainerRef = useRef<ArcherContainerHandle | null>(null);
  const refreshArcherArrows = useCallback(() => {
    archerContainerRef.current?.refreshScreen();
  }, []);

  const highlightedCalls = getHighlightedCalls(highlightedFunction, calls);

  return (
    <div className="h-screen">
      <Allotment>
        <Allotment vertical>
          <div className="w-full h-full overflow-auto p-6">
            <Toolbar />
            <ArcherContainer
              ref={archerContainerRef}
              noCurves
              strokeColor="#E2E8F0"
              strokeWidth={1}
              startMarker={false}
              endMarker={false}
            >
              {firstRoot ? (
                <CallChildren id={firstRoot} refreshArcherArrows={refreshArcherArrows} />
              ) : (
                <div className="flex justify-center items-center h-full">
                  <Spinner size="medium" />
                </div>
              )}
            </ArcherContainer>
          </div>
          <Allotment.Pane className="call-table" preferredSize={500}>
            <Table
              rows={highlightedCalls.map(({ fields = {} }) => fields)}
              rowIds={highlightedCalls.map(({ id }) => id)}
              onFocusChange={({ rowId }) => setSelectedId(rowId)}
            />
          </Allotment.Pane>
        </Allotment>

        <Allotment.Pane preferredSize={500}>
          <div className="bg-gray-50 w-full h-full overflow-auto">
            <DetailPane />
          </div>
        </Allotment.Pane>
      </Allotment>
    </div>
  );
};

const isUlid = (id: string) => /^[0123456789ABCDEFGHJKMNPQRSTVWXYZ]{26}$/.test(id);

const useTraceId = () => {
  const { traceId } = useParams();
  return traceId && isUlid(traceId) ? traceId : undefined;
};

export const TracePage = () => {
  const traceId = useTraceId();
  useEffect(() => {
    document.title =
      traceId && recipes[traceId]
        ? `${recipes[traceId].title} | Interactive Composition Explorer`
        : "Interactive Composition Explorer";
  }, []);

  return !traceId ? null : (
    <TreeProvider key={traceId} traceId={traceId}>
      <Trace traceId={traceId} />
    </TreeProvider>
  );
};
