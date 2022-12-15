interface FValue {
  source: string;
  value: string;
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
        return (
          <span key={i} title={part.source} className={`p2 bg-${color}-50 text-${color}-600`}>
            {part.formatted}
          </span>
        );
      })}
    </span>
  );
};
