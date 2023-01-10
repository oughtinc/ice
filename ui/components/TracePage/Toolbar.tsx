import { chain } from "lodash";
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  HStack,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Switch,
} from "@chakra-ui/react";
import { CallInfo, Calls, useTreeContext } from "/components/TracePage/TracePage";
import { ArrowsIn, ArrowsOut, CaretDown } from "phosphor-react";
import { CallFunction, CallName } from "/components/TracePage/CallName";

const SelectHighlightedFunction = () => {
  const { calls, highlightedFunction, setHighlightedFunction } = useTreeContext();
  const nameCounts = chain(calls)
    .values()
    .slice(1) // skip the root (a call that's hidden in the tree)

    // TODO this is working around a broken non-call object in the Calls
    //  that has the ID of the trace. This is a side effect of how children are emitted,
    //  and should be fixed properly at the source of the problem.
    .filter("name")

    .countBy(call => JSON.stringify([call.cls, call.name]))
    .value();

  const options = Object.keys(nameCounts)
    .sort()
    .map(nameJson => {
      const count = nameCounts[nameJson];
      const [cls, name] = JSON.parse(nameJson);
      return (
        <MenuItem
          key={nameJson}
          onClick={() => {
            setHighlightedFunction({ cls, name });
          }}
        >
          {/* TODO use tailwind instead */}
          <Box as="span" minWidth="3em" textAlign="right" marginRight="0.5em">
            {count} ×
          </Box>
          <CallName cls={cls} name={name} />
        </MenuItem>
      );
    });

  return (
    <span>
      <Menu>
        <MenuButton as={Button} rightIcon={<CaretDown />} variant="outline">
          {highlightedFunction ? <CallName {...highlightedFunction} /> : "Select function..."}
        </MenuButton>
        <MenuList>{options}</MenuList>
      </Menu>
    </span>
  );
};

export const isHighlighted = (call: CallInfo, highlightedFunction?: CallFunction) =>
  highlightedFunction &&
  call.name == highlightedFunction.name &&
  call.cls == highlightedFunction.cls;

export const getHighlightedCalls = (highlightedFunction: CallFunction | undefined, calls: Calls) =>
  Object.values(calls).filter(call => isHighlighted(call, highlightedFunction));

export const highlightedAncestors = (
  highlightedFunction: CallFunction | undefined,
  calls: Calls,
) => {
  const result: Record<string, true> = {};
  if (!highlightedFunction) return result;
  for (let call of Object.values(calls)) {
    if (isHighlighted(call, highlightedFunction)) {
      while (call) {
        result[call.parent] = true;
        call = calls[call.parent];
      }
    }
  }
  return result;
};

export const Toolbar = () => {
  const { highlightedFunction, setExpandedById, othersHidden, setOthersHidden, calls } =
    useTreeContext();
  return (
    // TODO use tailwind instead
    <HStack spacing="1.5em">
      <SelectHighlightedFunction />
      <HStack>
        <Button
          disabled={!highlightedFunction}
          onClick={() =>
            setExpandedById(expanded => ({
              ...expanded,
              ...highlightedAncestors(highlightedFunction, calls),
            }))
          }
          leftIcon={<ArrowsOut size="1.5em" />}
        >
          Expand
        </Button>
        <Button onClick={() => setExpandedById({})} leftIcon={<ArrowsIn size="1.5em" />}>
          Collapse all
        </Button>
      </HStack>
      <FormControl display="flex" alignItems="center">
        <FormLabel marginInlineEnd="5px" mb="0">
          Hide others
        </FormLabel>
        <Switch
          size="lg"
          checked={othersHidden}
          disabled={!highlightedFunction}
          onChange={event => setOthersHidden(event.target.checked)}
        />
      </FormControl>
    </HStack>
  );
};
