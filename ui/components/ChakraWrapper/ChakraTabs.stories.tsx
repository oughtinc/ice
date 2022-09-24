import { Tab, TabList, Tabs } from "@chakra-ui/react";
import { Fragment } from "react";

const story = { component: Tabs };
export default story;

const VARIANTS = ["line"] as const;
const COLOR_SCHEMES = ["blue"] as const;

export const Default = () => (
  <>
    {VARIANTS.map(variant => (
      <Fragment key={variant}>
        <div className="capitalize mb-2 mt-4">{variant}</div>
        <div className="grid grid-cols-4 gap-2">
          {COLOR_SCHEMES.map(colorScheme => (
            <Tabs key={`${variant}-${colorScheme}`}>
              <TabList className="mx-4">
                <Tab>Tab 1</Tab>
                <Tab>Tab 2</Tab>
                <Tab>Tab 3</Tab>
              </TabList>
            </Tabs>
          ))}
        </div>
      </Fragment>
    ))}
  </>
);
