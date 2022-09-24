import { ThemingInfo } from "./ChakraWrapper";

export const alertStyles = {
  baseStyle: () => ({
    borderRadius: "6px",
    fontWeight: "medium",
    justifyContent: "flex-start",
    textAlign: "left",
  }),
  variants: {
    subtle: (themingInfo: ThemingInfo) => {
      return {
        container: {
          color: `${themingInfo.colorScheme}.600`,
          backgroundColor: `${themingInfo.colorScheme}.50`,
          borderWidth: "1px",
          borderColor: `${themingInfo.colorScheme}.300`,
          borderRadius: "6px",
        },
      };
    },
  },
};
