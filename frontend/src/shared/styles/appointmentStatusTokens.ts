export const APPOINTMENT_STATUSES = ["reservado", "confirmado", "atendido", "ausente", "cancelado"] as const;

export type AppointmentStatus = (typeof APPOINTMENT_STATUSES)[number];

export interface StatusColorTokens {
  readonly text: string;
  readonly background: string;
  readonly border: string;
}

// Paleta AA (contraste texto/fondo >= 4.5:1), documentada en docs/evidencias/verify-C-25.md.
export const APPOINTMENT_STATUS_TOKENS: Readonly<Record<AppointmentStatus, StatusColorTokens>> = {
  reservado: { text: "#1D4ED8", background: "#DBEAFE", border: "#93C5FD" },
  confirmado: { text: "#15803D", background: "#DCFCE7", border: "#86EFAC" },
  atendido: { text: "#374151", background: "#E5E7EB", border: "#9CA3AF" },
  ausente: { text: "#B45309", background: "#FEF3C7", border: "#FCD34D" },
  cancelado: { text: "#B91C1C", background: "#FEE2E2", border: "#FCA5A5" },
};
