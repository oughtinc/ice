import { Button, forwardRef } from "@chakra-ui/react";
import { CaretDown, CaretRight, ChatCenteredDots } from "phosphor-react";

export const CallIconButton = forwardRef(
  (
    {
      expanded,
      onChange,
      childCount,
      isModelCall,
    }: {
      expanded: boolean;
      onChange: (expanded: boolean) => void;
      childCount: number;
      isModelCall: boolean;
    },
    ref,
  ) => (
    <Button
      className="rounded-full p-1 h-fit mr-2 !shadow-none hover:bg-slate-200 w-12"
      isActive={expanded}
      {...(isModelCall || !childCount
        ? {}
        : {
            "aria-label": expanded ? "Collapse" : "Expand",
            leftIcon: expanded ? <CaretDown /> : <CaretRight />,
            onClick: () => onChange(expanded),
          })}
      ref={ref}
      size="md"
      variant="outline"
    >
      <span className="mr-1">{isModelCall ? <ChatCenteredDots /> : childCount || "𝑓"}</span>
    </Button>
  ),
);
