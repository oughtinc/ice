import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { MainWrapper } from "./components/MainWrapper";
import { TracePage } from "./components/TracePage/TracePage";
import HomePage from "./pages/HomePage";
import TraceListPage from "./pages/TraceListPage";

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

createRoot(document.getElementById("root")!).render(
  <MainWrapper>
    <RouterProvider router={router} />
  </MainWrapper>,
);
