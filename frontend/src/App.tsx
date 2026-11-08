import { useState } from "react";
import { createBrowserRouter, Navigate, RouterProvider, type RouteObject } from "react-router-dom";
import { DEFAULT_AGENDA_TIMEZONE } from "./features/agenda/agendaConfig";
import { AgendaPage } from "./features/agenda/AgendaPage";
import { formatLocalDate } from "./features/agenda/agendaTime";
import { systemClock, type Clock } from "./features/agenda/clock";
import { AuthProvider } from "./features/auth/AuthContext";
import { PublicOnlyRoute } from "./features/auth/PublicOnlyRoute";
import { RequireAuth } from "./features/auth/RequireAuth";
import type { TokenStore } from "./features/auth/tokenStore";
import { LoginPage } from "./features/login/LoginPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import type { ApiClient, FetchFn } from "./shared/api/client";
import { AppShell } from "./shared/components/AppShell";

function RootRedirect({ clock }: { readonly clock: Clock }) {
  const today = formatLocalDate(clock.now(), DEFAULT_AGENDA_TIMEZONE);
  return <Navigate to={`/agenda?date=${today}`} replace />;
}

// eslint-disable-next-line react-refresh/only-export-components
export function createAppRoutes(clock: Clock = systemClock): RouteObject[] {
  return [
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
            { index: true, element: <RootRedirect clock={clock} /> },
            { path: "agenda", element: <AgendaPage clock={clock} /> },
            { path: "*", element: <NotFoundPage /> },
          ],
        },
      ],
    },
  ];
}

// eslint-disable-next-line react-refresh/only-export-components
export const routes: RouteObject[] = createAppRoutes();

export interface AppProps {
  tokenStore?: TokenStore;
  client?: ApiClient;
  fetchFn?: FetchFn;
  clock?: Clock;
}

export function App({ tokenStore, client, fetchFn, clock = systemClock }: AppProps = {}) {
  // El router se crea al montar, así toma la URL actual del navegador.
  const [router] = useState(() =>
    createBrowserRouter(createAppRoutes(clock), {
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
