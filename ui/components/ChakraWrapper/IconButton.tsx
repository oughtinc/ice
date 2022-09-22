// eslint-disable-next-line no-restricted-imports
import { IconButton as ChakraIconButton } from "@chakra-ui/react";
import { ComponentProps, forwardRef } from "react";

// eslint-disable-next-line react/display-name
export const IconButton = forwardRef<HTMLButtonElement, ComponentProps<typeof ChakraIconButton>>(
  (props, forwardedRef) => {
    return (
      <ChakraIconButton
        ref={forwardedRef}
        {...props}
        variant={props.variant ? `${props.variant}Icon` : "solidIcon"}
      />
    );
  },
);
