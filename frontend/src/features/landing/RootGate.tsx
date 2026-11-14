import { useLocation } from "react-router-dom";
import { LoadingState } from "../../shared/components/LoadingState";
import { useAuth } from "../auth/AuthContext";
import { RequireAuth } from "../auth/RequireAuth";
import { LandingPage } from "./LandingPage";

/**
 * Raíz de la aplicación. En "/" el anónimo ve la portada pública; con sesión (o en cualquier
 * otra ruta) actúa como guardia de autenticación, así que "/" autenticado sigue resolviéndose
 * por el índice hijo (RootRedirect, con replace) y el resto de las rutas exige sesión.
 */
export function RootGate() {
  const { status } = useAuth();
  const location = useLocation();

  if (location.pathname === "/") {
    if (status === "checking") {
      return <LoadingState />;
    }
    if (status === "anonymous") {
      return <LandingPage />;
    }
  }
  return <RequireAuth />;
}
