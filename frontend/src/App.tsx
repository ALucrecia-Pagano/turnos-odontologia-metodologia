import { useState } from "react";
import { createBrowserRouter, RouterProvider, type RouteObject } from "react-router-dom";
import { HomePage } from "./pages/HomePage";
import { NotFoundPage } from "./pages/NotFoundPage";

const routes: RouteObject[] = [
  { path: "/", element: <HomePage /> },
  { path: "*", element: <NotFoundPage /> },
];

export function App() {
  // El router se crea al montar, así toma la URL actual del navegador.
  const [router] = useState(() =>
    createBrowserRouter(routes, {
      future: {
        v7_relativeSplatPath: true,
        v7_fetcherPersist: true,
        v7_normalizeFormMethod: true,
        v7_partialHydration: true,
        v7_skipActionErrorRevalidation: true,
      },
    }),
  );
  return <RouterProvider router={router} future={{ v7_startTransition: true }} />;
}
