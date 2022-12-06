import { CSSObject } from "@chakra-ui/system";
import { omit } from "lodash";
import { ThemingInfo } from "./ChakraWrapper";

const HEIGHT_BY_SIZE = {
  xs: "1.75rem",
  sm: "2.125rem",
  md: "2.625rem",
  lg: "3rem",
};
const ICON_BUTTON_FONT_SIZE_BY_SIZE = {
  xs: "md",
  sm: "md",
  md: "lg",
  lg: "lg",
};
const FONT_SIZE_BY_SIZE = {
  xs: "xs",
  sm: "sm",
  md: "sm",
  lg: "md",
};
const ICON_FONT_SIZE_BY_SIZE = {
  xs: "xs",
  sm: "md",
  md: "md",
  lg: "md",
};
function addBaseStyles(
  styles: (themingInfo: ThemingInfo) => CSSObject,
): (themingInfo: ThemingInfo) => CSSObject {
  return themingInfo => {
    return {
      ...styles(themingInfo),
      cursor: "pointer",
      height: HEIGHT_BY_SIZE[themingInfo.size],
      fontSize: FONT_SIZE_BY_SIZE[themingInfo.size],
      ["& span.chakra-button__icon:nth-of-type(1)"]: {
        fontSize: ICON_FONT_SIZE_BY_SIZE[themingInfo.size],
      },
      ["& span.chakra-button__icon:nth-last-of-type(1)"]: {
        fontSize: ICON_FONT_SIZE_BY_SIZE[themingInfo.size],
      },
    };
  };
}

function addIconStyles(
  styles: (themingInfo: ThemingInfo) => CSSObject,
): (themingInfo: ThemingInfo) => CSSObject {
  return themingInfo => ({
    ...styles(themingInfo),
    width: HEIGHT_BY_SIZE[themingInfo.size],
    height: HEIGHT_BY_SIZE[themingInfo.size],
    fontSize: ICON_BUTTON_FONT_SIZE_BY_SIZE[themingInfo.size],
  });
}

function solidStyles(themingInfo: ThemingInfo): CSSObject {
  return {
    borderRadius: "6px",
    fontWeight: "medium",
    color: "white",
    backgroundColor: `${themingInfo.colorScheme}.600`,
    _hover: {
      backgroundColor: `${themingInfo.colorScheme}.700`,
    },
    ["&.pseudo-focus"]: {
      boxShadow:
        "0 0 0 2px var(--chakra-colors-white),0 0 0 5px var(--chakra-colors-blue-300) !important",
    },
  };
}

const ROUDED_PADDING_BY_SIZE = {
  xs: "0.625rem",
  sm: "0.875rem",
  md: "1.125rem",
  lg: "1.325rem",
};
function roundedStyles(themingInfo: ThemingInfo): CSSObject {
  return {
    ...solidStyles(themingInfo),
    borderRadius: "9999px",
    px: ROUDED_PADDING_BY_SIZE[themingInfo.size],
  };
}

function outlineStyles(themingInfo: ThemingInfo): CSSObject {
  return {
    color: `${themingInfo.colorScheme}.500`,
    borderWidth: "1px",
    borderStyle: "solid",
    fontWeight: "medium",
    borderColor: `${themingInfo.colorScheme}.200`,
    _hover: {
      color: `${themingInfo.colorScheme}.600`,
      backgroundColor: `${themingInfo.colorScheme}.100`,
    },
    _active: {
      color: `${themingInfo.colorScheme}.600`,
      backgroundColor: `${themingInfo.colorScheme}.100`,
    },
    ["& .chakra-button__icon, svg"]: {
      color: `${themingInfo.colorScheme}.400`,
      _hover: {
        color: `${themingInfo.colorScheme}.500`,
      },
    },
  };
}

function ghostStyles(themingInfo: ThemingInfo): CSSObject {
  return omit(outlineStyles(themingInfo), ["borderWidth", "borderStyle", "borderColor"]);
}

export const buttonStyles = {
  defaultProps: {
    colorScheme: "slate",
  },
  baseStyle: (themingInfo: ThemingInfo) => {
    return {
      borderRadius: themingInfo.size === "xs" || themingInfo.size === "sm" ? "4px" : "6px",
      fontWeight: "medium",
    };
  },
  sizes: {
    xs: {
      px: 2,
      // Reduce margin of left / right icons
      ["& span.chakra-button__icon:nth-of-type(1)"]: {
        marginInlineEnd: "0.25rem",
      },
      ["& span.chakra-button__icon:nth-last-of-type(1)"]: {
        marginInlineStart: "0.25rem",
      },
    },
    sm: {
      px: 3,
      // Reduce margin of left / right icons
      ["& span.chakra-button__icon:nth-of-type(1)"]: {
        marginInlineEnd: "0.25rem",
      },
      ["& span.chakra-button__icon:nth-last-of-type(1)"]: {
        marginInlineStart: "0.25rem",
      },
    },
    md: {
      px: 4,
      // Reduce margin of left / right icons
      ["& span.chakra-button__icon:nth-of-type(1)"]: {
        marginInlineEnd: "0.375rem",
      },
      ["& span.chakra-button__icon:nth-last-of-type(1)"]: {
        marginInlineStart: "0.375rem",
      },
    },
    lg: {
      px: 5,
      // Reduce margin of left / right icons
      ["& span.chakra-button__icon:nth-of-type(1)"]: {
        marginInlineEnd: "0.5rem",
      },
      ["& span.chakra-button__icon:nth-last-of-type(1)"]: {
        marginInlineStart: "0.5rem",
      },
    },
  },
  variants: {
    solid: addBaseStyles(solidStyles),
    rounded: addBaseStyles(roundedStyles),
    outline: addBaseStyles(outlineStyles),
    ghost: addBaseStyles(ghostStyles),
    solidIcon: addIconStyles(solidStyles),
    roundedIcon: addIconStyles(roundedStyles),
    outlinedIcon: addIconStyles(outlineStyles),
    ghostIcon: addIconStyles(ghostStyles),
  },
};
