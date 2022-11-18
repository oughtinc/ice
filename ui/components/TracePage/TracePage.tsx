import { Button, Collapse, Skeleton, useToast } from "@chakra-ui/react";
import classNames from "classnames";
import produce from "immer";
import { isEmpty, isString, last, omit, set } from "lodash";
import { CaretDown, CaretRight, ChatCenteredDots } from "phosphor-react";
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
import Separator from "./Separator";
import Spinner from "./Spinner";
import { recipes } from "/helpers/recipes";
import * as COLORS from "/styles/colors.json";
import { useParams } from "react-router";

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

interface CallInfo {
  parent: string;
  start: number;
  name: string;
  doc: string;
  args: Record<string, unknown>;
  source?: string;
  children?: Record<string, CallInfo>;
  records?: Record<string, CallInfo>;
  result?: unknown;
  end?: number;
}

type Calls = Record<string, CallInfo>;

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
  selectedId: string | undefined;
  setSelectedId: Dispatch<SetStateAction<string | undefined>>;
  getExpanded: (id: string) => boolean;
  setExpanded: (id: string, expanded: boolean) => void;
  getFocussed: (id: string) => boolean;
} | null>(null);

const applyUpdates = (calls: Calls, updates: Record<string, unknown>) =>
  Object.entries(updates).forEach(([path, value]) => set(calls, path, value));

const TreeProvider = ({ traceId, children }: { traceId: string; children: ReactNode }) => {
  const traceOffsetRef = useRef(0);
  const [calls, setCalls] = useState<Calls>({});
  const [selectedId, setSelectedId] = useState<string>();
  const [rootId, setRootId] = useState<string>("");
  const [expandedById, setExpandedById] = useState<Record<string, boolean>>({});
  const [autoselected, setAutoselected] = useState(false);

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

  useEffect(() => {
    let mounted = true;
    let timeoutId: ReturnType<typeof setTimeout>;

    const poll = async () => {
      let delay = 1_000;
      try {
        const urlPrefix = recipes[traceId] ? "https://oughtinc.github.io/static" : "/api";
        const url = `${urlPrefix}/traces/${traceId}.jsonl`;
        const offset = traceOffsetRef.current;
        const contentLength = await getContentLength(url);
        if (offset >= contentLength) return;

        const initialOffset = 1e6;
        const subsequentOffset = 1e7;
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
        if (!mounted) return;

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
        if (mounted) {
          timeoutId = setTimeout(poll, delay);
        }
      }
    };

    poll();

    return () => {
      mounted = false;
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

  return (
    <TreeContext.Provider
      value={{
        traceId,
        calls,
        rootId,
        selectedId,
        setSelectedId,
        getExpanded: (id: string) => expandedById[id] ?? false,
        setExpanded: (id: string, expanded: boolean) => {
          if (id !== rootId && !isModelCall(calls[id]))
            setExpandedById(current => ({ ...current, [id]: expanded }));
        },
        getFocussed,
      }}
    >
      {children}
    </TreeContext.Provider>
  );
};

const useTreeContext = () => {
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

type SelectedCallInfo = {
  parent: string;
  start: number;
  name: string;
  doc: string;
  args: Record<string, unknown>;
  source?: string;
  children?: Record<string, CallInfo>;
  records?: Record<string, CallInfo>;
  result?: unknown;
  end?: number;
  id: string;
};

const useSelectedCallInfo = (): SelectedCallInfo | undefined => {
  const { calls, selectedId } = useTreeContext();
  return selectedId ? { ...calls[selectedId], id: selectedId } : undefined;
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

const isModelCall = ({ name, args }: { name: string; args: Record<string, unknown> }) =>
  MODEL_CALL_NAMES.includes(name) &&
  (args as any).self?.class_name &&
  (args as any).self.class_name.includes("Agent");

const getFormattedName = (snakeCasedName: string) => {
  const spacedName = snakeCasedName.replace(/_/g, " ");
  const capitalizedAndSpacedName = spacedName[0].toUpperCase() + spacedName.slice(1);
  return capitalizedAndSpacedName;
};

const CallName = ({ className, id }: { className?: string; id: string }) => {
  const { name, args } = useCallInfo(id);
  const recipeClassName = (args as any).self?.class_name;
  const displayName =
    (name === "execute" || name === "run") && recipeClassName ? recipeClassName : name;
  const modelCall = isModelCall({ name, args });
  return (
    <div className="flex items-center gap-1">
      {recipeClassName && recipeClassName !== displayName ? (
        <span className={classNames(className, "text-gray-500")}>
          {getFormattedName(recipeClassName)}:
        </span>
      ) : undefined}
      <span className={className}>{getFormattedName(displayName)}</span>
    </div>
  );
};

function lineAnchorId(id: string) {
  return `line-anchor-${id}`;
}

const Call = ({ id, refreshArcherArrows }: { id: string; refreshArcherArrows: () => void }) => {
  const { name, args, children = {}, result, select, selected, focussed } = useCallInfo(id);
  const { selectedId } = useTreeContext();
  const { getParent } = useLinks();
  const childIds = Object.keys(children);
  const { expanded, setExpanded } = useExpanded(id);

  const modelCall = isModelCall({ name, args });
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
          className={classNames(
            "justify-start text-start items-start h-fit min-w-[300px] p-1.5 !shadow-none",
          )}
          variant="ghost"
          onClick={ev => {
            select();
            ev.stopPropagation();
          }}
          isActive={selected}
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
            {childIds.length > 0 ? (
              <Button
                aria-label={expanded ? "Collapse" : "Expand"}
                className={classNames(
                  "rounded-full p-1 h-fit mr-2 !shadow-none hover:bg-slate-200 w-12",
                )}
                leftIcon={modelCall ? undefined : expanded ? <CaretDown /> : <CaretRight />}
                size="md"
                isActive={expanded}
                variant="outline"
                onClick={event => {
                  setExpanded(!expanded);
                  // Theres a hard to debug layout thing here, where sometimes
                  // the arrows don't redraw properly when nodes are expanded.
                  setTimeout(() => refreshArcherArrows(), 50);
                }}
              >
                <span className={"mr-1"}>{modelCall ? <ChatCenteredDots /> : childIds.length}</span>
              </Button>
            ) : (
              <Button
                className={classNames(
                  "rounded-full p-1 h-fit mr-2 !shadow-none hover:bg-slate-200 w-12",
                )}
                size="md"
                variant="outline"
              >
                <span>𝑓</span>
              </Button>
            )}
          </ArcherElement>
          <div className="mx-2">
            <CallName className="text-base text-slate-700" id={id} />
            <div className="text-sm text-gray-600 flex items-center">
              <span className="text-indigo-600" title={JSON.stringify(getStrings(args), null, 4)}>
                {getShortString(getStrings(args)?.[0] || "()")}
              </span>
              <span className="px-2">→</span>
              {result === undefined ? <Spinner size="small" /> : <ResultComponent value={result} />}
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

const isObjectLike = (value: unknown): value is object =>
  value !== null && typeof value === "object";

const isArrayWithString = (value: unknown): value is unknown[] =>
  Array.isArray(value) && isString(value[0]);

const getFirstDescendant = (value: unknown): unknown => {
  if (isObjectLike(value) && !isArrayWithString(value)) {
    return getFirstDescendant(Object.values(value)[0]);
  }
  if (isArrayWithString(value)) {
    return value.filter(isString);
  }
  return value;
};

const getStrings = (value: any): string[] => {
  if (isObjectLike(value)) {
    if ("value" in value) {
      value = (value as any).value;
    } else {
      if ("self" in value) {
        value = omit(value, "self");
      }
      if ("record" in value) {
        value = omit(value, "record");
      }
    }
  }

  const result = getFirstDescendant(value);

  return Array.isArray(result) ? result : [`${result ?? "()"}`];
};

const getShortString = (string: any, maxLength: number = 35): string => {
  return string.length > maxLength ? string.slice(0, maxLength).trim() + "..." : string;
};

const ResultComponent = ({ value }: { value: any }): JSX.Element => {
  const strings = getStrings(value);

  return (
    <>
      {strings.map((string, idx) => (
        <div
          className="px-[4px] py-[2px] mx-[3px] bg-lightBlue-50 text-lightBlue-600 rounded-4"
          key={idx}
          title={string}
        >
          {getShortString(string)}
        </div>
      ))}
    </>
  );
};

type JsonChild =
  | { type: "array"; values: unknown[] }
  | { type: "object"; values: [string, unknown][] }
  | { type: "value"; value: unknown };

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
      else return { type: "object", values: Object.entries(data) };
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
      {value}
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
  info: SelectedCallInfo;
};

type Tab = "io" | "src";

const DetailPaneContent = ({ info }: DetailPaneContentProps) => {
  const { id, doc } = info;
  const [tab, setTab] = useState<Tab>("io"); // io for inputs and outputs, src for source

  return (
    <div className="flex-1 p-6">
      <TabHeader id={id} doc={doc} />
      <TabBar tab={tab} setTab={setTab} />
      <TabContent tab={tab} info={info} />
    </div>
  );
};

const TabHeader = ({ id, doc }: { id: string; doc: string }) => (
  <div className="mb-4">
    <h3 className="text-lg font-semibold text-gray-800">
      <CallName id={id} />
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
  const { args, records = {}, result, source } = info;

  return (
    <div className="space-y-4 mt-4">
      {tab === "io" ? (
        <InputOutputContent args={args} records={records} result={result} />
      ) : (
        <SourceContent source={source} />
      )}
    </div>
  );
};

type InputOutputContentProps = {
  args: any;
  records: any;
  result: any;
};

const excludeMetadata = (source: Record<string, unknown> | undefined) => {
  if (source === undefined) return undefined;
  return Object.fromEntries(
    Object.entries(source).filter(([key, value]) => !["self", "paper"].includes(key)),
  );
};

const InputOutputContent = ({ args, records, result }: InputOutputContentProps) => (
  <>
    <Json name="Inputs" value={excludeMetadata(args)} />
    {!isEmpty(records) && <Json name="Records" value={Object.values(records)} />}
    <Json name="Outputs" value={result} />
  </>
);

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
  const { selectedId, rootId, setSelectedId, getExpanded, setExpanded } = useTreeContext();
  const { getParent, getChildren, getPrior, getNext } = useLinks();

  const maybeSetSelectedId = useCallback(
    (update: (id: string) => string | undefined) => {
      setSelectedId(id => {
        const res = update(id as any) || id;
        console.log(res);
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
              console.log(rootId, selectedId);
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

  const [detailWidth, setDetailWidth] = useState(500);

  const firstRoot = getChildren(traceId)[0];

  const archerContainerRef = useRef<ArcherContainerHandle | null>(null);
  const refreshArcherArrows = useCallback(() => {
    archerContainerRef.current?.refreshScreen();
  }, []);

  return (
    <div className="flex flex-col h-full min-h-screen max-h-screen">
      <div className="flex divide-x divide-gray-100 flex-1 overflow-clip">
        <div className="flex-1 p-6 overflow-y-auto flex-shrink-0">
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

        <Separator detailWidth={detailWidth} setDetailWidth={setDetailWidth} />

        <div className="bg-gray-50 overflow-y-auto flex-shrink-0" style={{ width: detailWidth }}>
          <DetailPane />
        </div>
      </div>
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
