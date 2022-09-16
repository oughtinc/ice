import * as React from "react";
import { Components } from "react-markdown";
import {
  Code,
  Divider,
  Heading,
  Link,
  ListItem,
  OrderedList,
  Text,
  UnorderedList,
} from "@chakra-ui/layout";
import { Image } from "@chakra-ui/image";
import { Checkbox } from "@chakra-ui/checkbox";
import { Table, Tbody, Td, Th, Thead, Tr } from "@chakra-ui/table";
import { chakra } from "@chakra-ui/system";

type GetCoreProps = {
  children?: React.ReactNode;
  "data-sourcepos"?: any;
};

function getCoreProps(props: GetCoreProps): any {
  return props["data-sourcepos"] ? { "data-sourcepos": props["data-sourcepos"] } : {};
}

interface Defaults extends Components {
  heading?: Components["h1"];
}

export const defaults: Defaults = {
  p: props => {
    const { children } = props;
    return <Text mb={2}>{children}</Text>;
  },
  em: props => {
    const { children } = props;
    return <Text as="em">{children}</Text>;
  },
  blockquote: props => {
    const { children } = props;
    return (
      <Code as="blockquote" p={2}>
        {children}
      </Code>
    );
  },
  code: props => {
    const { inline, children, className } = props;

    if (inline) {
      return <Code p={2}>{children}</Code>;
    }

    return (
      <Code className={className} whiteSpace="break-spaces" display="block" w="full" p={2}>
        {" "}
        {children}
      </Code>
    );
  },
  del: props => {
    const { children } = props;
    return <Text as="del">{children}</Text>;
  },
  hr: props => {
    return <Divider />;
  },
  a: Link,
  img: Image,
  text: props => {
    const { children } = props;
    return <Text as="span">{children}</Text>;
  },
  ul: props => {
    const { ordered, children, depth } = props;
    const attrs = getCoreProps(props);
    let Element = UnorderedList;
    let styleType = "disc";
    if (ordered) {
      Element = OrderedList;
      styleType = "decimal";
    }
    if (depth === 1) styleType = "circle";
    return (
      <Element spacing={2} as={ordered ? "ol" : "ul"} styleType={styleType} pl={4} {...attrs}>
        {children}
      </Element>
    );
  },
  ol: props => {
    const { ordered, children, depth } = props;
    const attrs = getCoreProps(props);
    let Element = UnorderedList;
    let styleType = "disc";
    if (ordered) {
      Element = OrderedList;
      styleType = "decimal";
    }
    if (depth === 1) styleType = "circle";
    return (
      <Element spacing={2} as={ordered ? "ol" : "ul"} styleType={styleType} pl={4} {...attrs}>
        {children}
      </Element>
    );
  },
  li: props => {
    const { children, checked } = props;
    let checkbox = null;
    if (checked !== null && checked !== undefined) {
      checkbox = (
        <Checkbox isChecked={checked} isReadOnly>
          {children}
        </Checkbox>
      );
    }
    return (
      <ListItem {...getCoreProps(props)} listStyleType={checked !== null ? "none" : "inherit"}>
        {checkbox || children}
      </ListItem>
    );
  },
  heading: props => {
    const { level, children } = props;
    const sizes = ["2xl", "xl", "lg", "md", "sm", "xs"];
    return (
      <Heading my={4} as={`h${level}`} size={sizes[level - 1]} {...getCoreProps(props)}>
        {children}
      </Heading>
    );
  },
  pre: props => {
    const { children } = props;
    return <chakra.pre {...getCoreProps(props)}>{children}</chakra.pre>;
  },
  table: Table,
  thead: Thead,
  tbody: Tbody,
  tr: props => <Tr>{props.children}</Tr>,
  td: props => <Td>{props.children}</Td>,
  th: props => <Th>{props.children}</Th>,
};

// Liberated from https://github.com/mustaphaturhan/chakra-ui-markdown-renderer
// Fixed some bugs, simplified
const ChakraUIRenderer = (): Components => {
  const elements = {
    p: defaults.p,
    em: defaults.em,
    blockquote: defaults.blockquote,
    code: defaults.code,
    del: defaults.del,
    hr: defaults.hr,
    a: defaults.a,
    img: defaults.img,
    text: defaults.text,
    ul: defaults.ul,
    ol: defaults.ol,
    li: defaults.li,
    h1: defaults.heading,
    h2: defaults.heading,
    h3: defaults.heading,
    h4: defaults.heading,
    h5: defaults.heading,
    h6: defaults.heading,
    pre: defaults.pre,
    table: defaults.table,
    thead: defaults.thead,
    tbody: defaults.tbody,
    tr: defaults.tr,
    td: defaults.td,
    th: defaults.th,
  };

  return elements;
};

export default ChakraUIRenderer;
