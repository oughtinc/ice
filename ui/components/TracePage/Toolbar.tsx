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
      return (
        <MenuItem
          key={nameJson}
          onClick={() => {
            setHighlighted({ cls, name });
          }}
        >
          <Box as="span" minWidth="3em" textAlign="right" marginRight="0.5em">
            {count} ×
          </Box>
          <CallName {...{ cls, name }} />
        </MenuItem>
      );
    });

  return (
    <span>
      <Menu>
        <MenuButton as={Button} rightIcon={<CaretDown />} variant="outline">
          {highlighted ? <CallName {...highlighted} /> : "Select function..."}
        </MenuButton>
        <MenuList>{options}</MenuList>
      </Menu>
    </span>
  );
};

const highlightedAncestors = (highlighted: CallFunction | undefined, calls: Calls) => {
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

export function isHighlighted(call: CallInfo, highlighted?: CallFunction) {
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
          checked={hideOthers}
          disabled={!highlighted}
          onChange={event => setHideOthers(event.target.checked)}
        />
      </FormControl>
    </HStack>
  );
};
