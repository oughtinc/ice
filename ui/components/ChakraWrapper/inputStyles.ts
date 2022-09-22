export const inputStyles = {
  parts: ["addon", "field", "element"],
  variants: {
    outline: {
      element: {
        ["& .chakra-input__left-element, svg"]: {
          color: "slate.400",
        },
      },
      field: {
        borderRadius: "6px",
        borderColor: "slate.200",
        _hover: {
          borderColor: "slate.200",
        },
        _focus: {
          borderColor: "slate.200",
          boxShadow: "none",
        },
      },
    },
  },
};
