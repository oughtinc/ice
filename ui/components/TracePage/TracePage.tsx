import { ChevronRightIcon } from "@chakra-ui/icons";
import {
  Button,
  Collapse,
  IconButton,
  Skeleton,
  useColorModeValue,
  useToast,
} from "@chakra-ui/react";
import classNames from "classnames";
import produce from "immer";
import { isEmpty, last, omit, set } from "lodash";
import { useRouter } from "next/router";
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
import { JSONTree } from "react-json-tree";
import SyntaxHighlighter from "react-syntax-highlighter";
import Separator from "./Separator";
import Spinner from "./Spinner";

const chalkLikeStyle = {
  "hljs-keyword": { color: "rgb(45, 127, 232)" },
  "hljs-operator": { color: "rgb(45, 127, 232)" },
  "hljs-number": { color: "rgb(220, 50, 47)" },
  "hljs-decorator": { color: "rgb(45, 127, 232)" },
  "hljs-comment": { color: "rgb(133, 153, 0)" },
  "hljs-string": { color: "rgb(44, 137, 87)" },
  "hljs-built_in": { color: "rgb(220, 50, 47)" },
  "hljs-class": { color: "rgb(220, 50, 47)" },
  "hljs-module": { color: "rgb(220, 50, 47)" },
  "hljs-punctuation": { color: "rgb(28, 88, 56)" },
  "hljs-bracket": { color: "rgb(28, 88, 56)" },
  "hljs-plain": { color: "rgb(128, 128, 128)" },
};

const getContentLength = async (path: string) => {
  const response = await fetch(path, { method: "HEAD" });
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

const MODEL_CALL_NAMES = ["relevance", "answer", "predict", "classify", "prompted_classify"];

const TreeContext = createContext<{
  traceId: string;
  calls: Calls;
  selectedId: string | undefined;
  setSelectedId: Dispatch<SetStateAction<string | undefined>>;
  getExpanded: (id: string) => boolean;
  setExpanded: (id: string, expanded: boolean) => void;
} | null>(null);

const applyUpdates = (calls: Calls, updates: Record<string, unknown>) =>
  Object.entries(updates).forEach(([path, value]) => set(calls, path, value));

const TreeProvider = ({ traceId, children }: { traceId: string; children: ReactNode }) => {
  const traceOffsetRef = useRef(0);
  const [calls, setCalls] = useState<Calls>({});
  const [selectedId, setSelectedId] = useState<string>();
  const [expandedById, setExpandedById] = useState<Record<string, boolean>>({});
  const [autoselected, setAutoselected] = useState(false);

  useEffect(() => {
    if (!autoselected) {
      const firstRoot = Object.keys(calls[traceId]?.children ?? {})[0];
      if (firstRoot) {
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
        const path = `/traces/${traceId}.jsonl`;
        const offset = traceOffsetRef.current;
        const contentLength = await getContentLength(path);
        if (offset >= contentLength) return;

        const limit = Math.min(offset + 1e6, contentLength);
        if (limit < contentLength) delay = 50;

        const response = await fetch(path, {
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

  return (
    <TreeContext.Provider
      value={{
        traceId,
        calls,
        selectedId,
        setSelectedId,
        getExpanded: (id: string) => expandedById[id] ?? false,
        setExpanded: (id: string, expanded: boolean) =>
          setExpandedById(current => ({ ...current, [id]: expanded })),
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
  const { calls, selectedId, setSelectedId } = useTreeContext();
  return { ...calls[id], selected: selectedId === id, select: () => setSelectedId(id) };
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

const Name = ({ id }: { id: string }) => {
  const { name, args } = useCallInfo(id);
  const recipeClassName = (args as any).self?.class_name;
  return (
    <span>
      {(name === "execute" || name === "run") && recipeClassName
        ? "📋 " + recipeClassName
        : MODEL_CALL_NAMES.includes(name)
        ? "🕵 " + name
        : "💻 " + name}
    </span>
  );
};

const Call = ({ id }: { id: string }) => {
  const { args, children = {}, result, select, selected } = useCallInfo(id);
  const childIds = Object.keys(children);
  const { expanded, setExpanded } = useExpanded(id);

  const selectedBg = useColorModeValue("gray.100", "gray.700");
  const unselectedBg = useColorModeValue("transparent", "transparent");

  return (
    <div className="mt-2 flex-shrink-0">
      <div className="flex flex-shrink-0">
        {childIds.length ? (
          <IconButton
            aria-label={expanded ? "Collapse" : "Expand"}
            className="justify-center mx-1 flex-shrink-0 !shadow-none"
            icon={<ChevronRightIcon className={classNames({ "rotate-90": expanded })} />}
            size="s"
            variant="ghost"
            onClick={() => setExpanded(!expanded)}
            w="8"
          />
        ) : (
          <div className="mx-1 w-8" />
        )}
        <Button
          className="flex items-center flex-shrink-0 !shadow-none"
          size="s"
          variant="ghost"
          onClick={select}
          bg={selected ? selectedBg : unselectedBg}
          px="2"
          py="1"
        >
          <Name id={id} />
          <span className="pl-2 text-s text-gray-600 flex items-center">
            <span className="text-green-700">{getShortString(args)}</span>
            <span className="px-1">→</span>
            {result === undefined ? (
              <Spinner size="small" />
            ) : (
              <span className="text-blue-600">{getShortString(result)}</span>
            )}
          </span>
        </Button>
      </div>
      <Collapse in={expanded} transition={{ enter: { duration: 0 } }}>
        <div className="ml-6">{expanded && <CallChildren id={id} />}</div>
      </Collapse>
    </div>
  );
};

const CallChildren = ({ id }: { id: string }) => {
  const { children = {} } = useCallInfo(id) ?? {};
  const childIds = Object.keys(children);

  return (
    <div className="flex flex-col">
      {childIds.map(id => (
        <Call key={id} id={id} />
      ))}
    </div>
  );
};

const isObjectLike = (value: unknown): value is object =>
  value !== null && typeof value === "object";

const getFirstDescendant = (value: unknown): unknown =>
  isObjectLike(value) ? getFirstDescendant(Object.values(value)[0]) : value;

const getShortString = (value: any, maxLength: number = 35): string => {
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

  const string = `${getFirstDescendant(value) ?? "()"}`;
  return string.length > maxLength ? string.slice(0, maxLength).trim() + "..." : string;
};

const Json = ({ name, value }: { name: string; value: unknown }) => {
  const toast = useToast();
  return (
    <div>
      <div>{name}</div>
      {value === undefined ? (
        <Skeleton className="mt-4 h-4" />
      ) : (
        <JSONTree
          data={value}
          hideRoot
          theme={{
            tree: ({ style }) => ({
              style: { ...style, backgroundColor: undefined }, // remove default background
            }),
          }}
          valueRenderer={(valueAsString: string, value: unknown) =>
            typeof value === "string" ? (
              <div
                className="whitespace-pre-line break-normal select-none"
                onClick={() => {
                  navigator.clipboard.writeText(value);
                  toast({ title: "Copied to clipboard", duration: 1000 });
                }}
              >
                {value}
              </div>
            ) : (
              valueAsString
            )
          }
        />
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
      <Name id={id} />
    </h3>
    <p className="text-gray-600 text-sm">{doc}</p>
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

const InputOutputContent = ({ args, records, result }: InputOutputContentProps) => (
  <>
    <Json name="Inputs" value={args} />
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
      style={chalkLikeStyle}
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
  const { selectedId, setSelectedId, getExpanded, setExpanded } = useTreeContext();
  const { getParent, getChildren, getPrior, getNext } = useLinks();

  const maybeSetSelectedId = useCallback(
    (update: (id: string) => string | undefined) => setSelectedId(id => id && (update(id) || id)),
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
            ArrowDown: () => maybeSetSelectedId(id => getExpandedChildren(id)[0] || nextFrom(id)),
            ArrowLeft: () =>
              getExpandedChildren(selectedId).length
                ? setExpanded(selectedId, false)
                : maybeSetSelectedId(getParent),
            ArrowRight: () => getChildren(selectedId).length && setExpanded(selectedId, true),
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

  return (
    <div className="flex flex-col h-full min-h-screen">
      <div className="flex divide-x divide-gray-100 flex-1 overflow-clip">
        <div className="flex-1 p-6 overflow-y-auto flex-shrink-0">
          {firstRoot ? (
            <CallChildren id={firstRoot} />
          ) : (
            <div className="flex justify-center items-center h-full">
              <Spinner size="medium" />
            </div>
          )}
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
  const {
    query: { id },
  } = useRouter();
  const traceId = Array.isArray(id) ? id[0] : id;
  return traceId && isUlid(traceId) ? traceId : undefined;
};

export const TracePage = () => {
  const traceId = useTraceId();
  return !traceId ? null : (
    <TreeProvider key={traceId} traceId={traceId}>
      <Trace traceId={traceId} />
    </TreeProvider>
  );
};
