import { ThemingInfo } from "./ChakraWrapper";

export const tagStyles = {
  variants: {
    subtle: (themingInfo: ThemingInfo) => ({
      container: {
        fontWeight: 400,
        color: `${themingInfo.colorScheme}.500`,
        backgroundColor: `${themingInfo.colorScheme}.50`,
      },
    }),
  },
};
