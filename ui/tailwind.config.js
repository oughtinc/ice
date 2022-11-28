const COLORS = require("./styles/colors.json");

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./components/**/*.{ts,tsx}", "./pages/**/*.{ts,tsx}"],
  variants: {
    extend: {
      visibility: ["group-hover"],
      backgroundColor: ["group-hover"],
    },
  },
  theme: {
    extend: {
      width: {
        140: "35rem",
      },
      screens: {
        "has-hover": { raw: "(hover: hover)" },
      },
      flex: {
        2: "2 2 0%",
        3: "3 3 0%",
      },
    },
    colors: {
      transparent: "transparent",
      current: "currentColor",
      white: "#ffffff",
      ...COLORS,
    },
    borderRadius: {
      0: "0rem",
      4: "0.25rem",
      8: "0.5rem",
      full: "9999px",
    },
    maxWidth: {
      60: "15rem",
      72: "18rem",
      96: "24rem",
      160: "40rem",
      full: "100%",
    },
    maxHeight: {
      60: "15rem",
      72: "18rem",
      96: "24rem",
      160: "40rem",
      full: "100%",
    },
  },
  plugins: [require("tailwindcss-labeled-groups")(["nested"])],
  corePlugins: {
    preflight: false,
  },
};
