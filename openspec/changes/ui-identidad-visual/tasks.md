# Tasks

## 1. Línea base y preparación

- [ ] 1.1 Correr la suite completa del frontend (`npm test -- --run`) y registrar en `docs/evidencias/baseline-C-34.txt` el total de tests verdes; verificar que no haya fallos preexistentes.
- [ ] 1.2 Confirmar que solo `StatusBadge.test.tsx` y `appointmentStatusTokens.test.ts` quedan autorizados a cambiar (solo valores de color); documentar en `docs/evidencias/baseline-C-34.txt` que cualquier otro test roto obliga a frenar.
- [ ] 1.3 Agregar `@fontsource-variable/jost` y `@fontsource-variable/manrope` 5.3.0 a `frontend/package.json` e importarlos en `frontend/src/main.tsx`; verificar con `npm install` y `npm run build` que Vite empaqueta las fuentes sin URLs externas.

## 2. Paleta de identidad y tokens

- [ ] 2.1 Escribir primero el test de paleta en `frontend/src/shared/styles/tokens.test.ts` o en un test nuevo que verifique los valores de `--color-text`, `--color-text-muted`, `--color-background`, `--color-surface`, `--color-border`, `--color-primary`, `--color-primary-contrast`, `--color-focus`, `--color-navy`, `--color-accent` y `--color-ice`; verificar que falla (RED).
- [ ] 2.2 Actualizar `tokens.css` con la paleta Aqua y los tokens nuevos; verificar que el test de 2.1 pasa (GREEN).
- [ ] 2.3 Agregar el test de contraste de paleta (13.80:1, 5.83:1 y 5.91:1 para texto real; decorativos excluidos); verificar que falla antes del ajuste y pasa después.
- [ ] 2.4 Conservar `--font-family-base` y la primera declaración `font-family: var(--font-family-base)` en `reset.css`; correr `tokens.test.ts` sin cambios y verificar que sigue verde.

## 3. Colores de estado

- [ ] 3.1 Actualizar los valores de color en `appointmentStatusTokens.test.ts` con los nuevos pares y ratios; verificar que el test falla contra el mapa actual (RED).
- [ ] 3.2 Actualizar `appointmentStatusTokens.ts` con los cinco pares de la tabla del design; verificar que `appointmentStatusTokens.test.ts` pasa (GREEN).
- [ ] 3.3 Actualizar los valores de color esperados en `StatusBadge.test.tsx`; verificar que `StatusBadge.test.tsx` pasa y que ningún otro test se modificó.

## 4. Tipografías autoalojadas

- [ ] 4.1 Agregar el test de fuentes que verifique `--font-family-heading` con `"Jost Variable"` y `--font-family-body` con `"Manrope Variable"`, ambos con fallback al system stack; verificar que falla (RED).
- [ ] 4.2 Definir ambos tokens en `tokens.css` y agregar la segunda declaración `font-family: var(--font-family-body)` en `body` de `reset.css`; verificar que el test de 4.1 y `tokens.test.ts` pasan (GREEN).
- [ ] 4.3 Aplicar `var(--font-family-heading)` a títulos y `var(--font-family-body)` a texto en los estilos existentes; verificar con `npm run build` y con el test de fuentes.
- [ ] 4.4 Agregar el test que verifica ausencia de `fonts.googleapis.com`, `fonts.gstatic.com` y URLs de CDN en `frontend/src`; verificar que pasa y que las fuentes salen del bundle de Vite.

## 5. Barra única con marca

- [ ] 5.1 Agregar el test de `AppShell` que verifique una sola barra, el logo, "Aqua" y "Clínica Odontológica" en escritorio; verificar que falla (RED).
- [ ] 5.2 Integrar el logo `logo-aqua-oscuro.png` y los textos de marca en `AppShell.tsx`, fuera de `nav`; verificar que el test de 5.1 y `AppShell.test.tsx` pasan (GREEN).
- [ ] 5.3 Agregar el test de estructura de la barra que verifique que renderiza el logo, "Aqua" y el subtítulo "Clínica Odontológica" dentro de un elemento con la clase que el CSS oculta en `max-width: 768px`; el test no afirma anchos, renglones ni visibilidad responsive (eso es verificación visual). Verificar que falla antes del CSS y pasa después.
- [ ] 5.4 Ajustar `AppShell.module.css` con `flex-wrap`, la clase del subtítulo oculto en `max-width: 768px` y el máximo de dos renglones; verificar con el test de estructura 5.3. La captura a 768 px queda a cargo de Claude en la verificación independiente (task 8.5), no se ejecuta en apply.

## 6. Login: logo y carrusel

- [ ] 6.1 Agregar el test del logo del login que verifique `logo-aqua-claro.png` sobre fondo oscuro y el heading accesible "Turnos Odontología"; verificar que falla (RED).
- [ ] 6.2 Integrar el logo claro y conservar el heading en `LoginPage.tsx` y `LoginPage.module.css`; verificar que el test de 6.1, `LoginPage.test.tsx` y `smoke.test.tsx` pasan (GREEN).
- [ ] 6.3 Escribir los tests del carrusel con ticker inyectado: inicia en `hero-1-sala-de-espera`, avanza al llamar al callback, vuelve a la primera tras la quinta, pausa detiene el avance, reduced motion desactiva rotación y Ken Burns, y el ticker se cancela al desmontar; verificar que fallan (RED).
- [ ] 6.4 Implementar el carrusel y `createIntervalTicker(7000)` con las props `ticker` y `prefersReducedMotion`; verificar que los tests de 6.3 pasan (GREEN).
- [ ] 6.5 Agregar el test de accesibilidad del carrusel: cinco imágenes con `alt=""`, `aria-hidden="true"`, `data-slide-index` y `data-active` solo en la activa; verificar que pasa.
- [ ] 6.6 Implementar el Ken Burns de 7 s `ease-out` que se reinicia por foto activa y el botón Pausar/Reanudar con `aria-pressed`; verificar con los tests de 6.3 y 6.5 y con `npm run build`.

## 7. Créditos

- [ ] 7.1 Agregar la sección de créditos en `README.md` con las cinco fotografías, el logo de Aqua y la licencia SIL OFL de Jost y Manrope vía Fontsource; verificar leyendo la sección y confirmando que no inventa fotógrafos.
- [ ] 7.2 Agregar el test o chequeo de documentación que verifique la existencia de la sección de créditos; verificar que pasa.

## 8. Evidencias y verificación visual

- [ ] 8.1 Generar `docs/evidencias/red-C-34/` con la salida RED de cada test nuevo y verificar que cada archivo corresponde a un escenario del spec.
- [ ] 8.2 Crear `docs/evidencias/mutaciones-C-34.py` a partir del patrón de `mutaciones-C-28.py` (una mutación por test nuevo) y ejecutarlo; verificar que cada mutación invalida el test por su aserción propia. El script debe incluir un detector de mutaciones inválidas (la mutación aplicada no matchea el texto, o el test falla por error de sintaxis/import en vez de por aserción), respetar CRLF, restaurar el original y reportar `SHA-256 sin cambios: si` al final, más un `RESUMEN` con totales, mutaciones muertas e inválidas (estas últimas deben dar 0); generar `mutaciones-C-34.txt`.
- [ ] 8.3 Crear `docs/evidencias/trazabilidad-C-34.py` y `verify-C-34.md` que mapeen cada escenario del spec a su test y a su mutación; los escenarios de verificación visual (barra a 768 px) se marcan como tales y no se mapean a mutación; verificar que no queden escenarios sin cobertura.
- [ ] 8.4 Correr la suite completa y verificar que solo cambiaron `StatusBadge.test.tsx` y `appointmentStatusTokens.test.ts`; si falla cualquier otro test, frenar y reportar.
- [ ] 8.5 Verificación visual en 1440 px y 768 px (Playwright) a cargo de Claude en la verificación independiente: barra en uno/dos renglones, logo correcto en login y barra, carrusel sin recortes y estados legibles; registrar el resultado en `verify-C-34.md`. **A cargo de Claude**: el apply NO ejecuta esta task y la deja sin marcar.
- [ ] 8.6 Confirmar que todas las evidencias (`baseline`, `red`, `mutaciones`, `trazabilidad`, `verify`) están en UTF-8 y sin datos reales de pacientes.
- [ ] 8.7 Ejecutar `npx tsc --noEmit` y `npx eslint` desde `frontend/`, registrar el comando y el código de salida en `docs/evidencias/verify-C-34.md`; verificar que ambos terminan con código 0.
- [ ] 8.8 Revisar `git diff` de los tests existentes: solo se aceptan líneas agregadas, salvo los valores de color en `StatusBadge.test.tsx` y `appointmentStatusTokens.test.ts`; si cualquier otro test existente cambia o falla, frenar y reportar.
- [ ] 8.9 Correr la suite completa de Vitest y registrar en `docs/evidencias/verify-C-34.md` la cantidad de tests antes y después; verificar que la diferencia sea solo la de los tests nuevos.

## Workflow follow-up

- Archivar el change `ui-identidad-visual` después de que Claude complete la verificación visual independiente y la suite quede verde.
- Sincronizar los delta specs con `openspec/specs/frontend-foundation` y `openspec/specs/frontend-auth-session` al archivar.
