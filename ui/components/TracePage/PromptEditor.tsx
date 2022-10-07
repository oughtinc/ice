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
            className="rounded-4 border-slate-200 border flex-grow px-3 py-2 whitespace-pre-wrap"
            contentEditable
            onChange={ev => setCurrentPrompt((ev.target as HTMLSpanElement).innerText)}
          >
            {currentPrompt}
          </div>
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
            >
              Prompt model
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
