import type { UserRole } from "../../shared/api/types";

export interface MenuItem {
  readonly id: string;
  readonly label: string;
  readonly path: string;
  readonly disabled: boolean;
  readonly badge: "Próximamente";
}

interface MenuDefinition {
  readonly id: string;
  readonly label: string;
  readonly path: string;
  readonly roles: readonly UserRole[];
}

const MENU_DEFINITIONS: readonly MenuDefinition[] = [
  {
    id: "agenda",
    label: "Agenda",
    path: "/agenda",
    roles: ["administrador", "recepcion", "odontologo"],
  },
  {
    id: "turnos",
    label: "Turnos",
    path: "/turnos",
    roles: ["administrador", "recepcion"],
  },
  {
    id: "horarios-y-bloqueos",
    label: "Horarios y bloqueos",
    path: "/horarios-y-bloqueos",
    roles: ["administrador", "recepcion", "odontologo"],
  },
  {
    id: "catalogos",
    label: "Catálogos",
    path: "/catalogos",
    roles: ["administrador", "recepcion", "odontologo"],
  },
  {
    id: "pacientes",
    label: "Pacientes",
    path: "/pacientes",
    roles: ["administrador", "recepcion", "odontologo"],
  },
  {
    id: "usuarios-y-roles",
    label: "Usuarios y roles",
    path: "/usuarios-y-roles",
    roles: ["administrador"],
  },
];

export function menuFor(role: UserRole): readonly MenuItem[] {
  return MENU_DEFINITIONS.filter((item) => item.roles.includes(role)).map(
    (item) => ({
      id: item.id,
      label: item.label,
      path: item.path,
      disabled: true,
      badge: "Próximamente" as const,
    }),
  );
}
