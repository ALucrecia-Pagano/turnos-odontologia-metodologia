import { Navigate, Outlet, useLocation } from "react-router-dom";
import { LoadingState } from "../../shared/components/LoadingState";
import { useAuth } from "./AuthContext";

export function RequireAuth() {
  const { status, lastEvent } = useAuth();
  const location = useLocation();

  if (status === "checking") {
    return <LoadingState />;
  }

  if (status === "anonymous") {
    if (lastEvent === "manual") {
      return <Navigate to="/login" replace />;
    }
    return (
      <Navigate
        to="/login"
        replace
        state={{
          from: `${location.pathname}${location.search}`,
          expired: lastEvent === "expired",
        }}
      />
    );
  }

  return <Outlet />;
}
