# Exploración – Identidad visual “Aqua — Clínica Odontológica”

Fecha: 2026-11-09
Repo: turnos-odontologia
Change: **C-34 `ui-identidad-visual`**

## a) Tests potencialmente rotos al aplicar las nuevas decisiones

| Decisión | Test afectado | Motivo del rompimiento |
|----------|---------------|------------------------|
| Nuevos colores de los tokens de estado (p. ej. `reservado` → `#1F5F86/#E4F2F8`) | `frontend/src/shared/components/StatusBadge.test.tsx` | Verifica estilos `color` y `backgroundColor` con valores hard-codeados. Cambiar los tokens hará que los `expect(...).toHaveStyle` fallen. **Autorizado a cambiar solo valores de color.** |
| Modificación de los tokens de estado (texto/fondo/border) | `frontend/src/shared/styles/appointmentStatusTokens.test.ts` | Compara valores exactos y ratios de contraste. Los nuevos colores provocarán fallos en los `expect(...).toBe` y en los checks de contraste. **Autorizado a cambiar solo valores de color.** |
| Paleta de tokens semánticos (ink, navy, primary, …) | `frontend/src/shared/styles/tokens.test.ts` | Solo comprueba espaciado, tipografía y foco. No se rompe si se conservan `--color-focus` en hex, `--font-family-base` con el system stack exacto y la declaración `font-family: var(--font-family-base)` en `body` de `reset.css`. |
| Tipografías nuevas | `frontend/src/shared/styles/tokens.test.ts` | Se evita el rompimiento agregando `--font-family-heading` y `--font-family-body` como tokens nuevos, sin tocar `--font-family-base`. |
| Unificación de barra de encabezado (una sola barra) | `frontend/src/shared/components/AppShell.test.tsx` | El test consulta los botones con `within(nav)`; mientras el `nav` y el botón de cierre de sesión existan, no falla. La marca/logo debe quedar **fuera** de `nav`. |
| Logo y textos de marca en el login | `frontend/src/test/smoke.test.tsx` | Exige un heading accesible con el nombre “Turnos Odontología”. Se conserva ese heading al integrar el logo claro. |
| Carrusel en la pantalla de login | No hay tests existentes que dependan del carrusel, por lo que **no se rompe**. |
| Logo en la barra | No hay tests que verifiquen la variante del logo, **no se rompe**. |

> **Resumen:** solo `StatusBadge.test.tsx` y `appointmentStatusTokens.test.ts` pueden cambiar (valores de color). Cualquier otro test que falle obliga a frenar y avisar antes de tocar código.

## b) Estrategia de test para el carrusel (regla C1: tests deterministas)

1. **Inyección de dependencias**
   - `ticker` → función `(callback: () => void) => () => void` que registra el callback y devuelve la cancelación.
   - `prefersReducedMotion` → prop opcional (`boolean`), por defecto `false`.
   - No se pasa `intervalMs`: el default es `createIntervalTicker(7000)`, pero los tests usan el ticker inyectado.
2. **Renderizado**
   ```tsx
   render(
     <LoginCarousel
       images={images}
       ticker={createTicker}
       prefersReducedMotion={false}
     />
   );
   ```
3. **Avance mediante el ticker**
   ```ts
   const advance = getAdvanceCallback(); // devuelto por createTicker
   act(() => advance()); // pasa a la siguiente foto
   expect(document.querySelector('[data-slide-index="1"]')).toHaveAttribute('data-active', 'true');
   ```
4. **Escenarios mínimos**
   - Avanza al siguiente slide y vuelve a la primera después de la quinta.
   - `aria-pressed="true"` con texto “Reanudar” detiene el avance: al llamar al callback la foto activa no cambia.
   - Cuando `prefersReducedMotion` es true, no hay avance automático ni efecto Ken Burns.
   - El ticker se cancela en el cleanup del `useEffect` al desmontar.
5. **Identificación de fotos**
   - Cada foto lleva `data-slide-index="${i}"` y solo la activa lleva `data-active="true"`.
   - Todas las fotos son decorativas: `alt=""` y `aria-hidden="true"` (no solo la inactiva).
6. **Sin timers reales ni mocks** – el test controla el tiempo mediante el ticker, cumpliendo la regla C1.

## c) Decisiones cerradas

| Tema | Opciones | Decisión |
|------|----------|----------|
| Duración del intervalo del carrusel | 2 s, 3 s, 5 s, 7 s | **7 s** (balance legibilidad/dinamismo). |
| Orden de las fotos | Cualquiera | **Comenzar con `hero-1-sala-de-espera.webp`**. |
| Logo en login (fondo oscuro) vs barra (fondo claro) | Lógica dinámica | **`logo-aqua-claro.png` en el login (fondo oscuro) y `logo-aqua-oscuro.png` en la barra (fondo claro)**, sin detección dinámica de tema. |
| Texto en la barra | Solo “Aqua” o “Aqua” + “Clínica Odontológica” | **Logo + “Aqua” + “Clínica Odontológica” en escritorio; en tablet (≤ 768 px) solo “Aqua”.** |
| Animación Ken Burns | 7 s ease-out (reinicia cada foto) | **Sí, 7 s ease-out**. |
| Botón pausa/reanudar | Siempre visible vs solo en hover | **Siempre visible** con `aria-pressed` y texto “Pausar”/“Reanudar”. |
| Atributos de accesibilidad de fotos decorativas | `alt=""` y `aria-hidden="true"` | **Ambos en las cinco fotos**. |

## d) Logo: variantes (PNG decodificados y medidos)

No había visor de imágenes disponible para el modelo, así que se decodificaron los PNG y se midió la luminancia media de los píxeles opacos:

| Archivo | Tamaño | Luminancia media | Lectura | Uso |
|---------|--------|------------------|---------|-----|
| `logo-aqua-claro.png` | 1124×278 | 202 | Logo claro | Fondo oscuro → **login** |
| `logo-aqua-oscuro.png` | 1124×278 | 78.8 | Logo oscuro/navy | Fondo claro → **barra** |
| `isotipo-aqua-claro.png` | — | clara | Isotipo claro | Fondo oscuro |
| `isotipo-aqua.png` | — | oscura | Isotipo oscuro | Fondo claro |
| `logo-variantes.png` | 2800×720 | — | Lámina de referencia | No es asset de UI |

## e) Borrador de entrada para `CHANGES.md`

```
C-34: ui-identidad-visual
-------------------------
**Propósito**: Aplicar la identidad visual “Aqua — Clínica Odontológica” a toda la UI existente.

**Alcance**:
- Paleta de tokens en `frontend/src/shared/styles/tokens.css` (ink, navy, primary, accent, ice, fondo, texto secundario, foco).
- Colores de estado en `appointmentStatusTokens.ts` con contraste ≥ 4.5:1.
- Tipografías Jost (títulos) y Manrope (texto) mediante `@fontsource-variable` (sin CDN).
- Logo en `frontend/src/assets/brand/` (variante clara para login oscuro, oscura para barra clara).
- Barra única: logo + “Aqua” + “Clínica Odontológica” (tablet solo “Aqua”), máximo dos renglones a 768 px.
- Carrusel en el login (5 fotos, 7 s, Ken Burns 7 s ease-out, pausa/reanudar, respeta `prefers-reduced-motion`).
- Créditos en `README.md` con fotos, logo y licencias de fuentes.

**Exclusiones**:
- No se modifica lógica de dominio ni API.
- Solo se actualizan valores de color en `StatusBadge.test.tsx` y `appointmentStatusTokens.test.ts`; ningún otro test se modifica.

**Dependencias**:
- Depende de **C-28** (`ui-agenda-semanal`). Se ejecuta antes de **C-29**.

**Ubicación en el roadmap**:
- Fase 6 (UI). No pertenece a un “hito 6” ni a una “fase UI-Visual”; se inserta después de **C-28** y antes de **C-29**.
```

## f) Uso de la skill `appointment-frontend-ux`

- **Checklist** seguida: lectura de KB, verificación de tokens, accesibilidad, regla C1 (tests deterministas, sin mocks), verificación visual (desktop 1440 px y tablet 768 px).
- **Context7** se consultó en esta sesión; el detalle de cada llamada está en §Uso del MCP.
- La regla C1 se refiere a los **tests**, no a la accesibilidad.
- Rutas reales confirmadas: login en `frontend/src/features/login/LoginPage.tsx` (ruta `/login` en `frontend/src/App.tsx`); shell en `frontend/src/shared/components/AppShell.tsx`.

## Uso del MCP

Todas las llamadas se hicieron en esta sesión con el MCP `context7`. No se enviaron datos de pacientes, tokens ni secretos; solo nombres de librerías y consultas técnicas.

### 1. `context7_resolve-library-id` — Fontsource

**Herramienta:** `context7_resolve-library-id`

**Parámetros:**

| Parámetro | Valor |
|---|---|
| `libraryName` | `Fontsource` |
| `query` | `self-hosted variable fonts with Fontsource in a Vite React app` |

**Resultado (candidatos relevantes):**

| Título | Library ID |
|---|---|
| Fontsource | `/fontsource/fontsource` |
| Fontsource (sitio) | `/websites/fontsource` |
| Fontsource Font Files | `/fontsource/font-files` |
| Fontsource (DeepWiki) | `/websites/deepwiki_fontsource_fontsource` |
| Google Font Metadata | `/fontsource/google-font-metadata` |

**ID elegido:** `/fontsource/fontsource`, por ser el paquete principal y el que documenta los imports de fuentes variables.

### 2. `context7_query-docs` — Fontsource

**Herramienta:** `context7_query-docs`

**Parámetros:**

| Parámetro | Valor |
|---|---|
| `libraryId` | `/fontsource/fontsource` |
| `query` | `import variable fonts in Vite React, wght.css entry point, font-family name for Jost and Manrope` |
| `language` | `TypeScript` |

**Aporte:**

- El import por defecto del paquete variable incluye todos los pesos: `import "@fontsource-variable/open-sans";`.
- Para cargar solo el eje de peso: `import "@fontsource-variable/open-sans/wght.css";`.
- Las fuentes estáticas se importan por peso: `import "@fontsource/open-sans/400.css";`.
- La familia se referencia con el sufijo `Variable` (p. ej. `"Open Sans Variable"`), criterio que se aplica a `"Jost Variable"` y `"Manrope Variable"`.
- Los archivos quedan empaquetados por Vite; no hace falta CDN ni `<link>`.

**Verificación adicional:** `npm view @fontsource-variable/jost version` y `npm view @fontsource-variable/manrope version` devolvieron **5.3.0** para ambos paquetes.

### 3. `context7_resolve-library-id` — Vite

**Herramienta:** `context7_resolve-library-id`

**Parámetros:**

| Parámetro | Valor |
|---|---|
| `libraryName` | `Vite` |
| `query` | `static asset imports and CSS handling in Vite 5` |

**Resultado (candidatos relevantes):**

| Título | Library ID | Versiones listadas |
|---|---|---|
| Vite | `/vitejs/vite` | incluye `v5.4.21` |
| Vite (sitio) | `/websites/vite_dev` | — |
| Vite Guide | `/websites/vite_dev_guide` | — |
| Vite (CN) | `/websites/cn_vite_dev` | — |
| Vite LLMs | `/llmstxt/vite_dev_llms-full_txt` | — |

**ID elegido:** `/vitejs/vite`, porque lista la serie 5 que usa el repo (`vite@5`).

### 4. `context7_query-docs` — Vite

**Herramienta:** `context7_query-docs`

**Parámetros:**

| Parámetro | Valor |
|---|---|
| `libraryId` | `/vitejs/vite` |
| `query` | `importing static assets like images and CSS in Vite 5, asset URL handling and types` |
| `language` | `TypeScript` |

**Aporte:**

- Importar una imagen devuelve la URL pública resuelta: `import imgUrl from './img.png'`.
- Los assets importados se incluyen en el build con hash; no se referencian por ruta manual.
- Para tipos de assets en TypeScript se usa `/// <reference types="vite/client" />` (o `vite/client` en `tsconfig`).
- Las URLs en CSS (`url()`) se resuelven y reescriben automáticamente.
- Conclusión: los logos y las cinco fotos se importan estáticamente desde `frontend/src/assets/`, y las fuentes de Fontsource se empaquetan sin configuración extra.

## Correcciones de la revisión

- **Identificador:** C-34 (no C-31, que ya existe).
- **Dependencia:** C-28 (`ui-agenda-semanal`); se ejecuta **antes de C-29**.
- **C-26 es el login**, no C-28.
- **Roadmap:** no existe “hito 6” ni “fase UI-Visual”; C-34 se ubica en Fase 6 (UI), después de C-28 y antes de C-29.
- **Context7:** se elimina la afirmación de que no se había consultado. Las cuatro llamadas reales de esta sesión quedaron documentadas en §Uso del MCP.
- **Regla C1:** es una regla de **tests** (deterministas, sin timers reales ni mocks), no de accesibilidad.
- **Rutas reales:** `frontend/src/features/login/LoginPage.tsx`, `frontend/src/shared/components/AppShell.tsx` y `frontend/src/App.tsx`.
- **Logo:** se decodificaron los PNG y se midió su luminancia; el mapeo definitivo quedó en §d.
- **Barra:** logo + “Aqua” + “Clínica Odontológica” (no “Aqua — Clínica Odontológica” en un solo texto); en tablet solo “Aqua”.
- **Tests:** solo `StatusBadge.test.tsx` y `appointmentStatusTokens.test.ts` cambian (valores de color). Se conservan `--font-family-base`, `--color-focus`, el heading “Turnos Odontología” y los tokens de agenda.
