import { chain } from "lodash";
import { ChangeEvent } from "react";
import { Button, FormControl, FormLabel, HStack, Select, Switch } from "@chakra-ui/react";
import { CallInfo, Calls, getFormattedName, useTreeContext } from "/components/TracePage/TracePage";

const SelectHighlightedFunction = () => {
  const { calls, highlighted, setHighlighted } = useTreeContext();
  const nameCounts = chain(calls)
    .values()
    .slice(1) // skip the root
    .filter("name")
    .countBy(call => JSON.stringify([call.cls, call.name]))
    .value();

  const options = Object.keys(nameCounts)
    .sort()
    .map(nameJson => {
      const count = nameCounts[nameJson];
      const [cls, name] = JSON.parse(nameJson);
      let label = `${getFormattedName(name)} (${count})`;
      if (cls) {
        label = getFormattedName(cls) + " : " + label;
      }
      return (
        <option key={nameJson} value={nameJson}>
          {label}
        </option>
      );
    });

  const onChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const nameJson = event.target.value;
    if (!nameJson) return;
    const [cls, name] = JSON.parse(nameJson);
    setHighlighted({ cls, name });
  };

  return (
    <span style={{ maxWidth: "50%" }}>
      <Select
        placeholder="Select function..."
        onChange={onChange}
        value={JSON.stringify([highlighted?.cls, highlighted?.name])}
      >
        {options}
      </Select>
    </span>
  );
};

const highlightedAncestors = (highlighted: Highlighted | undefined, calls: Calls) => {
  const result: Record<string, true> = {};
  if (!highlighted) return result;
  for (let call of Object.values(calls)) {
    if (isHighlighted(call, highlighted)) {
      while (call) {
        result[call.parent] = true;
        call = calls[call.parent];
      }
    }
  }
  return result;
};

export interface Highlighted {
  name: string; // function name
  cls?: string; // class name for methods
}

export function isHighlighted(call: CallInfo, highlighted?: Highlighted) {
  return call.name == highlighted?.name && call.cls == highlighted?.cls;
}

export const Toolbar = () => {
  const { highlighted, setExpandedById, hideOthers, setHideOthers, calls } = useTreeContext();
  return (
    <HStack spacing="1.5em">
      <SelectHighlightedFunction />
      <HStack>
        <Button
          disabled={!highlighted}
          onClick={() =>
            setExpandedById(expanded => ({
              ...expanded,
              ...highlightedAncestors(highlighted, calls),
            }))
          }
        >
          Expand
        </Button>
        <Button onClick={() => setExpandedById({})}>Collapse all</Button>
      </HStack>
      <FormControl display="flex" alignItems="center">
        <FormLabel marginInlineEnd="5px" mb="0">
          Hide others
        </FormLabel>
        <Switch
          size="lg"
          checked={hideOthers}
          disabled={!highlighted}
          onChange={event => setHideOthers(event.target.checked)}
        />
      </FormControl>
    </HStack>
  );
};
