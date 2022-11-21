import React from "react";
import ReactDOM from "react-dom";
import "/styles/globals.css";
import { css, Global } from "@emotion/react";
import { ChakraWrapper } from "/components/ChakraWrapper/ChakraWrapper";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import HomePage from "/pages/HomePage";
import TraceListPage from "/pages/TraceListPage";
import { TracePage } from "/components/TracePage/TracePage";

const router = createBrowserRouter([
  {
    path: "/",
    element: <HomePage />,
  },
  {
    path: "traces/",
    element: <TraceListPage />,
  },
  {
    path: "traces/:traceId",
    element: <TracePage />,
  },
]);

const GlobalStyles = css`
  // Remove Chakra focus outline is the element is not actually focussed
  // See https://github.com/chakra-ui/chakra-ui/issues/708
  [data-focus]:not(:focus) {
    box-shadow: none !important;
  }
  // TODO (jason) Fixed in https://github.com/chakra-ui/chakra-ui/pull/5969,
  // but we can't upgrade till we remove Mui
  .chakra-popover__popper {
    min-width: unset !important;
  }

  * {
    box-sizing: border-box;
  }

  html,
  body,
  #__next {
    margin: 0;
    padding: 0;
    height: 100%;
  }

  h1,
  h2,
  h3 {
    margin: 0;
    padding: 0;
  }

  body {
    font-family: Roboto, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Oxygen, Ubuntu,
      Cantarell, Fira Sans, Droid Sans, Helvetica Neue, sans-serif;
    line-height: 1.5;
  }

  a {
    text-decoration: none;
  }

  a,
  a:visited {
    color: #3d90fb;
  }

  a:hover {
    cursor: pointer;
  }

  main {
    flex-grow: 1;
    display: flex;
    flex-flow: column;
  }
`;

ReactDOM.render(
  <React.StrictMode>
    <ChakraWrapper>
      <Global styles={GlobalStyles} />
      <RouterProvider router={router} />
    </ChakraWrapper>
  </React.StrictMode>,
  document.getElementById("root"),
);
