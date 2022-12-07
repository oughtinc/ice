import { Button } from "@chakra-ui/react";
import { CaretDown, CaretRight, ChatCenteredDots } from "phosphor-react";

export function CallIconButton({
  expanded,
  onChange,
  childCount,
  isModelCall,
}: {
  expanded: boolean;
  onChange: (expanded: boolean) => void;
  childCount: number;
  isModelCall: boolean;
}) {
  const expandable = !isModelCall && childCount > 0;
  return (
    <Button
      className="rounded-full p-1 h-fit mr-2 !shadow-none hover:bg-slate-200 w-12"
      isActive={expanded}
      {...(!expandable
        ? {}
        : {
            "aria-label": expanded ? "Collapse" : "Expand",
            leftIcon: expanded ? <CaretDown /> : <CaretRight />,
            onClick: () => onChange(expanded),
          })}
      size="md"
      variant="outline"
    >
      <span className="mr-1">{isModelCall ? <ChatCenteredDots /> : childCount || "𝑓"}</span>
    </Button>
  );
}
