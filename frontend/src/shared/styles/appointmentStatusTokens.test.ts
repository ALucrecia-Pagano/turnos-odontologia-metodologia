import { APPOINTMENT_STATUSES, APPOINTMENT_STATUS_TOKENS } from "./appointmentStatusTokens";

function channel(hexPair: string): number {
  const value = Number.parseInt(hexPair, 16) / 255;
  return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
}

function relativeLuminance(hex: string): number {
  const red = channel(hex.slice(1, 3));
  const green = channel(hex.slice(3, 5));
  const blue = channel(hex.slice(5, 7));
  return 0.2126 * red + 0.7152 * green + 0.0722 * blue;
}

function contrastRatio(foreground: string, background: string): number {
  const lighter = Math.max(relativeLuminance(foreground), relativeLuminance(background));
  const darker = Math.min(relativeLuminance(foreground), relativeLuminance(background));
  return (lighter + 0.05) / (darker + 0.05);
}

describe("APPOINTMENT_STATUS_TOKENS", () => {
  it("el mapa cubre los cinco estados sin undefined", () => {
    expect(APPOINTMENT_STATUSES).toEqual(["reservado", "confirmado", "atendido", "ausente", "cancelado"]);
    for (const status of ["reservado", "confirmado", "atendido", "ausente", "cancelado"] as const) {
      const tokens = APPOINTMENT_STATUS_TOKENS[status];
      expect(tokens, status).toBeDefined();
      expect(tokens.text, status).toMatch(/^#[0-9A-F]{6}$/);
      expect(tokens.background, status).toMatch(/^#[0-9A-F]{6}$/);
      expect(tokens.border, status).toMatch(/^#[0-9A-F]{6}$/);
    }
  });

  it("cada par texto y fondo cumple contraste AA", () => {
    const expected = {
      reservado: { text: "#1D4ED8", background: "#DBEAFE", ratio: "5.49" },
      confirmado: { text: "#15803D", background: "#DCFCE7", ratio: "4.57" },
      atendido: { text: "#374151", background: "#E5E7EB", ratio: "8.33" },
      ausente: { text: "#B45309", background: "#FEF3C7", ratio: "4.51" },
      cancelado: { text: "#B91C1C", background: "#FEE2E2", ratio: "5.30" },
    } as const;

    for (const status of APPOINTMENT_STATUSES) {
      const tokens = APPOINTMENT_STATUS_TOKENS[status];
      const ratio = contrastRatio(tokens.text, tokens.background);
      expect(tokens.text, status).toBe(expected[status].text);
      expect(tokens.background, status).toBe(expected[status].background);
      expect(ratio.toFixed(2), status).toBe(expected[status].ratio);
      expect(ratio, status).toBeGreaterThanOrEqual(4.5);
    }
  });
});
