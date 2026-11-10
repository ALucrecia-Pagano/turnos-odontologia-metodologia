export const APPOINTMENT_STATUSES = ["reservado", "confirmado", "atendido", "ausente", "cancelado"] as const;

export type AppointmentStatus = (typeof APPOINTMENT_STATUSES)[number];

export interface StatusColorTokens {
  readonly text: string;
  readonly background: string;
  readonly border: string;
}

// Paleta AA (contraste texto/fondo >= 4.5:1), documentada en docs/evidencias/verify-C-25.md.
export const APPOINTMENT_STATUS_TOKENS: Readonly<Record<AppointmentStatus, StatusColorTokens>> = {
  reservado: { text: "#1F5F86", background: "#E4F2F8", border: "#9CC7D8" },
  confirmado: { text: "#146C43", background: "#DDF3E7", border: "#86EFAC" },
  atendido: { text: "#3D4A5C", background: "#E6EBF1", border: "#94A3B8" },
  ausente: { text: "#9A5B00", background: "#FDF0D5", border: "#F0C36D" },
  cancelado: { text: "#A8242C", background: "#FBE4E6", border: "#EFA3A3" },
};
