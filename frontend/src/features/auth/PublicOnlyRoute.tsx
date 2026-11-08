import { Navigate, Outlet, useLocation } from "react-router-dom";
import { LoadingState } from "../../shared/components/LoadingState";
import { useAuth } from "./AuthContext";
import { safeInternalPath } from "./safeInternalPath";

function extractFromPath(state: unknown): unknown {
  if (typeof state === "object" && state !== null && "from" in state) {
    return (state as { from?: unknown }).from;
  }
  return undefined;
}

export function PublicOnlyRoute() {
  const { status } = useAuth();
  const location = useLocation();

  if (status === "checking") {
    return <LoadingState />;
  }

  if (status === "authenticated") {
    const destination = safeInternalPath(extractFromPath(location.state));
    return <Navigate to={destination} replace />;
  }

  return <Outlet />;
}
