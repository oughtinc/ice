import { ThemingInfo } from "./ChakraWrapper";

export const tabStyles = {
  variants: {
    line: (themingInfo: ThemingInfo) => ({
      tab: {
        paddingBottom: "8px",
        color: "blueGray.400",
        _selected: {
          color: `${themingInfo.colorScheme}.500`,
        },
        _active: {
          bg: "none",
        },
      },
      tablist: {
        borderColor: "blueGray.100",
      },
    }),
  },
};
