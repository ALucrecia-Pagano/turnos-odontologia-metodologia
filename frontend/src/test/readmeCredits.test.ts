import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const readme = readFileSync(resolve(process.cwd(), "../README.md"), "utf8");

describe("README credits", () => {
  it("documenta las fotografías, el logo y la licencia de las tipografías", () => {
    expect(readme).toContain("## Créditos");
    expect(readme).toContain("hero-1-sala-de-espera.webp");
    expect(readme).toContain("hero-2-consultorio.webp");
    expect(readme).toContain("hero-3-dentista.webp");
    expect(readme).toContain("hero-4-instrumental.webp");
    expect(readme).toContain("hero-5-sillon.webp");
    expect(readme).toContain("logo-aqua-claro.png");
    expect(readme).toContain("logo-aqua-oscuro.png");
    expect(readme).toContain("SIL Open Font License 1.1");
    expect(readme).toContain("Fontsource");
  });
});
