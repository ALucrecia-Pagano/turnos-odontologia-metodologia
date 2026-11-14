import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

describe("AgendaSpacing — Espaciado de página y encabezado", () => {
  it("11-espaciado-agenda: reduce separación entre título y toolbar y asigna margen superior con tokens al encabezado de fecha", () => {
    // 1. PageShell.module.css: espacio reducido entre título (header) y toolbar (primer hijo de main)
    const pageShellPath = path.resolve(__dirname, "../../shared/components/PageShell.module.css");
    const pageShellCss = fs.readFileSync(pageShellPath, "utf-8");

    // En escritorio, padding superior de main reducido a var(--space-3) (no var(--space-6))
    expect(pageShellCss).toMatch(/\.main\s*\{[^}]*padding:\s*var\(--space-3\)/);
    expect(pageShellCss).not.toMatch(/\.main\s*\{[^}]*padding:\s*var\(--space-6\)\s*var\(--space-5\);/);

    // En móvil (<= 640px), padding compacto con var(--space-2)
    expect(pageShellCss).toMatch(/@media\s*\(max-width:\s*640px\)/);
    expect(pageShellCss).toMatch(/@media\s*\(max-width:\s*640px\)[^{]*\{[\s\S]*?\.main\s*\{[^}]*padding:\s*var\(--space-2\)/);

    // Solo tokens, sin px hardcodeados
    expect(pageShellCss).not.toMatch(/padding:\s*\d+px/);

    // 2. AgendaView.module.css: margen superior al encabezado de fecha para no pegarse a la toolbar
    const agendaViewPath = path.resolve(__dirname, "./AgendaView.module.css");
    const agendaViewCss = fs.readFileSync(agendaViewPath, "utf-8");

    expect(agendaViewCss).toMatch(/\.headerBar\s*\{[^}]*margin-top:\s*var\(--space-4\)/);
    expect(agendaViewCss).not.toMatch(/margin-top:\s*\d+px/);
  });
});
