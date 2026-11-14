import { Navigate } from "react-router-dom";
import { DEFAULT_AGENDA_TIMEZONE } from "../agenda/agendaConfig";
import { formatLocalDate } from "../agenda/agendaTime";
import type { Clock } from "../agenda/clock";

export function RootRedirect({ clock }: { readonly clock: Clock }) {
  const today = formatLocalDate(clock.now(), DEFAULT_AGENDA_TIMEZONE);
  return <Navigate to={`/agenda?date=${today}`} replace />;
}
