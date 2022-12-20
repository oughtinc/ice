interface FValue {
  source: string;
  value: any;
  formatted: string;
}

export type FStringPart = string | FValue;

export const FString = ({ parts }: { parts: FStringPart[] }) => {
  let oddValue = false;
  return (
    <span>
      {parts.map((part, i) => {
        if (typeof part === "string") {
          return <span key={i}>{part}</span>;
        }
        const color = oddValue ? "lightBlue" : "indigo";
        oddValue = !oddValue;
        const inner = part.formatted;

        // This commented code allows seeing the original nested construction,
        // if the value isn't flattened in the trace.
        // const inner =
        //   typeof part.value === "object" && "__fstring__" in part.value ? (
        //     <FString parts={part.value.__fstring__ as FStringPart[]} />
        //   ) : (
        //     part.formatted
        //   );

        return (
          <span
            key={i}
            title={part.source}
            className={`p2 bg-${color}-50 text-${color}-600`}
            // style={{
            //   border: "1px solid #ccc",
            //   borderRadius: "4px",
            //   padding: "1px 2px",
            //   display: "inline-block",
            // }}
          >
            {inner}
          </span>
        );
      })}
    </span>
  );
};
