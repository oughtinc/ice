import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { MainWrapper } from "./components/MainWrapper";
import { TracePage } from "./components/TracePage/TracePage";
import HomePage from "./pages/HomePage";
import TraceListPage from "./pages/TraceListPage";

const storedPrefix = localStorage.getItem("OughtIcePrefix") || "";

const userPrefix = prompt("Enter a prefix for your traces", storedPrefix) || "";

const prefix =
  userPrefix === "" || userPrefix[userPrefix.length - 1] === "/" ? userPrefix : userPrefix + "/";

localStorage.setItem("OughtIcePrefix", prefix);

window.history.pushState({}, "", prefix);

const router = createBrowserRouter([
  {
    path: prefix + "",
    element: <HomePage />,
  },
  {
    path: prefix + "traces/",
    element: <TraceListPage />,
  },
  {
    path: prefix + "traces/:traceId",
    element: <TracePage />,
  },
]);

createRoot(document.getElementById("root")!).render(
  <MainWrapper>
    <RouterProvider router={router} />
  </MainWrapper>,
);
