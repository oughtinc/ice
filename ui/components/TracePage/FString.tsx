interface FValue {
  source: string;
  value: any;
  formatted: string;
}

export type FlattenedFStringPart = string | FValue;
export type RawFStringPart = FlattenedFStringPart | { __fstring__: RawFStringPart[] };

export function flattenFString(parts: RawFStringPart[]): FlattenedFStringPart[] {
  return parts.flatMap(part => {
    if (typeof part === "object") {
      if ("__fstring__" in part) {
        return flattenFString(part.__fstring__);
      }
      if (typeof part.value === "object" && "__fstring__" in part.value) {
        return flattenFString(part.value.__fstring__ as RawFStringPart[]);
      }
    }
    return [part];
  });
}

export const FString = ({ parts }: { parts: FlattenedFStringPart[] }) => {
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

        return (
          <span key={i} title={part.source} className={`p2 bg-${color}-50 text-${color}-600`}>
            {inner}
          </span>
        );
      })}
    </span>
  );
};
