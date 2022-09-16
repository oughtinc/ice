import { ThemingInfo } from "./ChakraWrapper";

export const buttonStyles = {
  defaultProps: {
    colorScheme: "blueGray",
  },
  baseStyle: () => ({
    borderRadius: "6px",
    fontWeight: "medium",
    justifyContent: "flex-start",
    textAlign: "left",
  }),
  variants: {
    customVariant: (themingInfo: ThemingInfo) => {
      return {
        color: "gray.600",
        borderWidth: "1px",
        borderStyle: "solid",
        borderColor: "gray.200",
        _hover: {
          borderColor: `${themingInfo.colorScheme}.500`,
          backgroundColor: `${themingInfo.colorScheme}.100`,
        },
        _active: {
          borderColor: "transparent",
          color: `${themingInfo.colorScheme}.500`,
          backgroundColor: `${themingInfo.colorScheme}.100`,
          _hover: {
            borderColor: `${themingInfo.colorScheme}.500`,
          },
        },
      };
    },
    outlined: (themingInfo: ThemingInfo) => {
      // Special case some things for now
      const isBlueGray = themingInfo.colorScheme === "blueGray";

      return {
        color: `${themingInfo.colorScheme}.500`,
        borderWidth: "1px",
        borderStyle: "solid",
        borderColor: `${themingInfo.colorScheme}.300`,
        _hover: {
          color: `${themingInfo.colorScheme}.600`,
          backgroundColor: `${themingInfo.colorScheme}.${isBlueGray ? "100" : "50"}`,
        },
        _active: {
          color: `${themingInfo.colorScheme}.600`,
          backgroundColor: `${themingInfo.colorScheme}.${isBlueGray ? "100" : "50"}`,
        },
      };
    },
    ghost: (themingInfo: ThemingInfo) => {
      return {
        color: `${themingInfo.colorScheme}.500`,
        _hover: {
          color: `${themingInfo.colorScheme}.600`,
          backgroundColor: `${themingInfo.colorScheme}.200`,
        },
        _active: {
          color: `${themingInfo.colorScheme}.600`,
          backgroundColor: `${themingInfo.colorScheme}.200`,
        },
      };
    },
    lightGhost: (themingInfo: ThemingInfo) => {
      // Special case some things for now
      const isBlueGray = themingInfo.colorScheme === "blueGray";

      return {
        color: `${themingInfo.colorScheme}.600`,
        fontWeight: 400,
        _hover: {
          backgroundColor: `${themingInfo.colorScheme}.${isBlueGray ? "100" : "50"}`,
        },
        _active: {
          backgroundColor: `${themingInfo.colorScheme}.${isBlueGray ? "100" : "50"}`,
        },
      };
    },
  },
};
