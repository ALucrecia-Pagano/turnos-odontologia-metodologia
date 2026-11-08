import { useState } from "react";
import { createBrowserRouter, RouterProvider, type RouteObject } from "react-router-dom";
import { AuthProvider } from "./features/auth/AuthContext";
import { PublicOnlyRoute } from "./features/auth/PublicOnlyRoute";
import { RequireAuth } from "./features/auth/RequireAuth";
import type { TokenStore } from "./features/auth/tokenStore";
import { LoginPage } from "./features/login/LoginPage";
import { HomePage } from "./pages/HomePage";
import { NotFoundPage } from "./pages/NotFoundPage";
import type { ApiClient, FetchFn } from "./shared/api/client";
import { AppShell } from "./shared/components/AppShell";

// eslint-disable-next-line react-refresh/only-export-components
export const routes: RouteObject[] = [
  {
    path: "/login",
    element: <PublicOnlyRoute />,
    children: [{ index: true, element: <LoginPage /> }],
  },
  {
    path: "/",
    element: <RequireAuth />,
    children: [
      {
        element: <AppShell />,
        children: [
          { index: true, element: <HomePage /> },
          { path: "*", element: <NotFoundPage /> },
        ],
      },
    ],
  },
];

export interface AppProps {
  tokenStore?: TokenStore;
  client?: ApiClient;
  fetchFn?: FetchFn;
}

export function App({ tokenStore, client, fetchFn }: AppProps = {}) {
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
  return (
    <AuthProvider tokenStore={tokenStore} client={client} fetchFn={fetchFn}>
      <RouterProvider router={router} future={{ v7_startTransition: true }} />
    </AuthProvider>
  );
}
