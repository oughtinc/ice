import { Button, Checkbox, Select } from "@chakra-ui/react";
import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";

const PromptEditorContext = createContext<{
  open: boolean;
  currentPrompt: string;
  setCurrentPrompt: (val: string | ((prev: string) => string)) => void;
  openEditor: (content: string) => void;
  closeEditor: () => void;
} | null>(null);

function saveCaretPosition(context: any, plusOne?: boolean) {
  var sel = window.getSelection();
  if (!sel || sel.rangeCount < 1) return;
  var selection = sel;
  var range = selection.getRangeAt(0);
  if (!range) return;
  range.setStart(context, 0);
  var len = range.toString().length;

  return function restore() {
    try {
      var pos = getTextNodeAtPosition(context, len);
      selection.removeAllRanges();
      var range = new Range();
      range.setStart(pos.node, pos.position + (plusOne ? 1 : 0));
      selection.addRange(range);
    } catch (e) {
      // pass
    }
  };
}

function getTextNodeAtPosition(root: any, index: any) {
  const NODE_TYPE = NodeFilter.SHOW_TEXT;
  var treeWalker = document.createTreeWalker(root, NODE_TYPE, function next(elem: any) {
    if (index > elem?.textContent?.length) {
      index -= elem?.textContent?.length;
      return NodeFilter.FILTER_REJECT;
    }
    return NodeFilter.FILTER_ACCEPT;
  });
  var c = treeWalker.nextNode();
  return {
    node: c ? c : root,
    position: index,
  };
}

export const PromptEditorProvider = ({ children }: { children: ReactNode }) => {
  const [open, setOpen] = useState(false);
  const [currentPrompt, setCurrentPrompt] = useState("");

  const openEditor = useCallback(content => {
    setOpen(true);
    setCurrentPrompt(content);
  }, []);
  const closeEditor = useCallback(() => setOpen(false), []);

  return (
    <PromptEditorContext.Provider
      value={{
        open,
        currentPrompt,
        setCurrentPrompt,
        openEditor,
        closeEditor,
      }}
    >
      {children}
    </PromptEditorContext.Provider>
  );
};

export const usePromptEditorContext = () => {
  const context = useContext(PromptEditorContext);
  if (!context)
    throw new Error("usePromptEditorContext must be used within a PromptEditorProvider");
  return context;
};

export const PromptEditorModal = () => {
  const { open, currentPrompt, setCurrentPrompt, closeEditor } = usePromptEditorContext();
  const promptBoxRef = useRef<HTMLDivElement | null>(null);
  const promptContentRef = useRef<HTMLDivElement | null>(null);

  const [promptResult, setPromptResult] = useState("");

  useEffect(() => {
    if (!open) return () => false;

    const closeOnEscape = (ev: KeyboardEvent) => {
      if (ev.key === "Escape") {
        closeEditor();
      }
    };

    document.addEventListener("keyup", closeOnEscape);
    return () => document.removeEventListener("keyup", closeOnEscape);
  }, [open, closeEditor]);

  useEffect(() => {
    if (!promptContentRef.current || !promptResult.length) return;
    const span = document.createElement("span");
    span.id = "promptResult";
    span.style.backgroundColor = "skyblue";
    span.appendChild(document.createTextNode(promptResult));
    const oldSpan = document.getElementById("promptResult");
    if (!oldSpan) promptContentRef.current.appendChild(span);
    else promptContentRef.current.replaceChild(span, oldSpan);
  }, [promptResult]);

  const handleInput = useCallback(
    (ev: any) => {
      setCurrentPrompt((ev.target as HTMLSpanElement).innerText);
    },
    [setCurrentPrompt],
  );

  useEffect(() => {
    if (!promptContentRef.current) return;
    const restore = saveCaretPosition(promptContentRef.current, currentPrompt.endsWith("\n"));
    promptContentRef.current.textContent = currentPrompt;
    if (restore) restore();
  }, [currentPrompt]);

  return (
    <div
      className={`${
        open ? "flex" : "hidden"
      } h-screen w-screen absolute top-0 left-0 bg-gray-200 bg-opacity-50 z-50 justify-center items-center cursor-pointer`}
      onClick={ev => {
        if (!promptBoxRef.current?.contains(ev.target as Node)) {
          closeEditor();
        }
      }}
    >
      <div
        className="rounded-4 px-6 py-4 bg-white h-2/3 w-2/3 shadow cursor-default flex gap-6"
        ref={promptBoxRef}
      >
        <div className="flex flex-col">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Prompt</h3>
          <div
            className="rounded-4 border-slate-200 border flex-grow px-3 py-2 whitespace-pre-wrap inline-block"
            contentEditable
            onInput={ev => handleInput(ev)}
            ref={promptContentRef}
          />
        </div>
        <div className="flex flex-col w-48">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Agent</h3>
          <label className="text-sm mb-1 text-gray-600">Model</label>
          <Select>
            <option>GPT-3</option>
            <option>AGI-1</option>
            <option>Roko&apos;s Basilisk</option>
          </Select>
          <label className="text-sm mb-1 mt-3 text-gray-600">Multiline</label>
          <Checkbox />
          <div className="flex-grow"></div>
          <div>
            <Button
              aria-label="prompt language model"
              className="rounded-4 px-2 py-1 h-fit !shadow-none hover:bg-slate-200 mt-4 text-xs"
              size="md"
              variant="outline"
              onClick={() => {
                setTimeout(() => setPromptResult("The quick brown fox"), 500);
                setTimeout(
                  () => setPromptResult("The quick brown fox jumps over the lazy dog."),
                  1000,
                );
              }}
            >
              Prompt model
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
