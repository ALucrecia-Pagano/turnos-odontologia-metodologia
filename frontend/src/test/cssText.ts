import { readFileSync } from "node:fs";
import { resolve } from "node:path";

export interface CssBlock {
  /** Prefijo de at-rule que envuelve el bloque ("" si está en el nivel superior). */
  readonly context: string;
  readonly selector: string;
  readonly body: string;
}

/** Lee un archivo relativo a `src/` (los tests corren con cwd en `frontend/`). */
export function readSrcFile(relativePath: string): string {
  return readFileSync(resolve(process.cwd(), "src", relativePath), "utf-8");
}

function stripComments(css: string): string {
  return css.replace(/\/\*[\s\S]*?\*\//g, "");
}

/** Recorre el CSS y devuelve todos los bloques con declaraciones, con su contexto de at-rule. */
export function cssBlocks(css: string): CssBlock[] {
  const source = stripComments(css);
  const blocks: CssBlock[] = [];

  function walk(start: number, context: string): number {
    let index = start;
    let prelude = "";
    while (index < source.length) {
      const char = source.charAt(index);
      if (char === "}") {
        return index + 1;
      }
      if (char === "{") {
        const head = prelude.trim().replace(/\s+/g, " ");
        if (head.startsWith("@")) {
          const nestedContext = context === "" ? head : `${context} ${head}`;
          index = walk(index + 1, nestedContext);
        } else {
          const close = source.indexOf("}", index);
          blocks.push({ context, selector: head, body: source.slice(index + 1, close).trim() });
          index = close + 1;
        }
        prelude = "";
        continue;
      }
      prelude += char;
      index += 1;
    }
    return index;
  }

  walk(0, "");
  return blocks;
}

/** Cuerpo de la regla con ese selector exacto y ese contexto; "" si no existe. */
export function ruleBody(css: string, selector: string, context = ""): string {
  const found = cssBlocks(css).find((block) => block.selector === selector && block.context === context);
  return found?.body ?? "";
}
