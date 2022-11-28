import { ChakraProvider, extendTheme } from "@chakra-ui/react";
import createCache from "@emotion/cache";
import { CacheProvider } from "@emotion/react";
import { ReactNode } from "react";
import { alertStyles } from "./alertStyles";
import { buttonStyles } from "./buttonStyles";
import { inputStyles } from "./inputStyles";
import { tabStyles } from "./tabsStyles";
import { tagStyles } from "./tagStyles";
import { textareaStyles } from "./textareaStyles";
import * as COLORS from "/styles/colors.json";

const emotionCache = createCache({
  key: "emotion-css-cache",
  prepend: true,
});

export interface ThemingInfo {
  colorMode: string; // eg light, dark
  colorScheme: string; // eg blue
  size: "xs" | "sm" | "md" | "lg";
}

const theme = extendTheme({
  components: {
    Input: inputStyles,
    Textarea: textareaStyles,
    Button: buttonStyles,
    Tag: tagStyles,
    Alert: alertStyles,
    Tabs: tabStyles,
  },
  colors: COLORS,
});

// TODO (jason) put the css reset in here
export const ChakraWrapper = ({ children }: { children: ReactNode }) => (
  <CacheProvider value={emotionCache}>
    <ChakraProvider resetCSS theme={theme}>
      {children}
    </ChakraProvider>
  </CacheProvider>
);
