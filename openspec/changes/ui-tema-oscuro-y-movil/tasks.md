# Tasks: ui-tema-oscuro-y-movil

## Reglas Obligatorias de Implementación
- **Regla C1 estricta**: Prohibido el uso de `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, fake timers (`vi.useFakeTimers`), MSW y `waitFor` prolongados. Si se requiere simulación de viewport o matchMedia, se inyecta como prop o helper inyectable, nunca como objeto global.
- **Sin bypass de tipos ni lint**: Prohibido el uso de `@ts-ignore`, `@ts-nocheck` o `eslint-disable`.
- **Tests existentes intocables**: Los tests existentes (`AppShell.test.tsx`, `menuFor.test.ts`, `AgendaToolbar.test.tsx`, `AgendaToolbar.nuevoTurno.test.tsx`, `AgendaView.test.tsx`, `AgendaGrid.accionable.test.tsx`, `AgendaTable.test.tsx`, `Dialog.test.tsx`, `Appointment*.test.tsx`) se mantienen 100% intactos. Todos los tests nuevos se confinan a archivos nuevos.
- **Trazabilidad 1:1 estricta**: Un escenario = un test = una mutación eliminada. Cada escenario testeable tiene su propio test unitario independiente; la suite de mutaciones debe fallar si dos escenarios comparten test.
- **Detección de mutaciones inválidas**: El script de mutaciones debe incluir detección explícita de mutaciones inválidas (código no compilable o mutación redundante).
- **Tokens y medidas**: Todos los colores, radios, espaciados y breakpoints se leen desde `tokens.css` o constantes semánticas documentadas (breakpoint de 640 px como `--breakpoint-mobile: 640px` o constante `MOBILE_BREAKPOINT`).
- **Accesibilidad**: Foco visible en controles interactivos (`:focus-visible`), área táctil mínima de 44×44 px en celular, estados con texto visible, ningún cambio de estado comunicado exclusivamente por color.
- **Tooling y salida**: `tsc --noEmit`, `npm run lint` y `npm run build` deben finalizar con código de salida 0.
- **Evidencias y plataforma**: Archivos de evidencia en codificación UTF-8 desde Git Bash.
- **Rama de trabajo**: `c36-apply`.

---

## 1. Línea Base y Preparación

- [x] 1.1 Crear la rama `c36-apply` desde `main` (`59ddd2e`) y verificar que la suite completa de frontend pasa intacta (260 tests pasando).
- [x] 1.2 Aplicar skill `appointment-frontend-ux` y consultar Context7 sobre soporte de CSS `scroll-snap`, `position: sticky` y `100dvh` dejando evidencia en `docs/skills-mcp/evidencias/C-36-context7.md`.
- [x] 1.3 Documentar el breakpoint móvil de 640 px (`--breakpoint-mobile: 640px`) y variables de layout de hoja inferior en `frontend/src/shared/styles/tokens.css`.

## 2. Barra Principal de la Aplicación (`AppShell`) y Menú Móvil

- [x] 2.1 **RED**: Escribir test unitario en `frontend/src/shared/components/AppShell.mobile.test.tsx` para cabecera compacta a <= 640 px con botón "Menú" accesible (`aria-expanded="false"`, `aria-controls="main-menu"`) ubicado fuera del elemento `<nav>`.
- [x] 2.2 **GREEN**: Implementar botón "Menú" y reorganización de cabecera en una fila para móvil en `AppShell.tsx` y `AppShell.module.css`.
- [x] 2.3 **RED**: Escribir test unitario en `frontend/src/shared/components/AppShell.mobile.test.tsx` para cierre del menú mediante tecla `Escape` y retorno de foco al botón "Menú".
- [x] 2.4 **GREEN**: Implementar handler de `Escape` y retorno de foco al cerrar el menú en `AppShell.tsx`.
- [x] 2.5 **REFACTOR**: Limpiar código y verificar que `AppShell.test.tsx` y `menuFor.test.ts` siguen 100% en verde e intactos.

## 3. Barra de Herramientas de Agenda (`AgendaToolbar`) y Panel de Filtros

- [x] 3.1 **RED**: Escribir test unitario en `frontend/src/features/agenda/AgendaToolbar.mobile.test.tsx` para la distribución compacta en dos filas (navegación/vista en fila 1, fecha/nuevo turno en fila 2) en viewports <= 640 px.
- [x] 3.2 **GREEN**: Implementar distribución en dos filas para móvil en `AgendaToolbar.tsx` y `AgendaToolbar.module.css`.
- [x] 3.3 **RED**: Escribir test unitario en `frontend/src/features/agenda/AgendaToolbar.mobile.test.tsx` para el botón "Filtros" con indicador de filtros activos ("Filtros (1)") y panel colapsable accesible.
- [x] 3.4 **GREEN**: Implementar botón de acceso a filtros con contador dinámico y panel plegable en `AgendaToolbar.tsx` y `AgendaToolbar.module.css`.
- [x] 3.5 **REFACTOR**: Limpiar código y verificar que `AgendaToolbar.test.tsx` y `AgendaToolbar.nuevoTurno.test.tsx` siguen 100% en verde e intactos.

## 4. Grilla de la Agenda con Scroll-Snap y Ancho Útil (`AgendaGrid`)

- [x] 4.1 **RED**: Escribir test unitario en `frontend/src/features/agenda/AgendaGrid.mobile.test.tsx` para contenedor con `scroll-snap-type: x mandatory` y columna de horas fija (`position: sticky`).
- [x] 4.2 **GREEN**: Implementar `scroll-snap` y estilos de eje horario sticky en `AgendaGrid.module.css` y `AgendaGrid.tsx`.
- [x] 4.3 **RED**: Escribir test unitario en `frontend/src/features/agenda/AgendaGrid.mobile.test.tsx` para dimensionamiento de columna al ancho útil y verificación de que el modo inicial de `AgendaView` sigue siendo `"grid"`.
- [x] 4.4 **GREEN**: Implementar cálculo de ancho de columna para móvil en `AgendaGrid.module.css` garantizando legibilidad de hora y paciente.
- [x] 4.5 **REFACTOR**: Limpiar código y verificar que `AgendaView.test.tsx` y `AgendaGrid.accionable.test.tsx` siguen 100% en verde e intactos.

## 5. Diálogos Modales como Hoja Inferior (Bottom Sheet)

- [x] 5.1 **RED**: Escribir test unitario en `frontend/src/shared/components/Dialog.bottomSheet.test.tsx` para la presentación de `Dialog` como hoja inferior a ancho completo con `max-height: 90dvh` y scroll interno en viewports <= 640 px.
- [x] 5.2 **GREEN**: Implementar estilos de hoja inferior en `Dialog.module.css` con esquinas superiores redondeadas y fijación al fondo de pantalla.
- [x] 5.3 **RED**: Escribir test unitario en `frontend/src/shared/components/Dialog.bottomSheet.test.tsx` para la preservación de modal flotante centrado de 580 px en pantallas >= 768 px.
- [x] 5.4 **GREEN**: Ajustar estilos en `AppointmentDetailDialog.module.css`, `AppointmentFormDialog.module.css` y `AppointmentRescheduleDialog.module.css` asegurando botones a 44 px sin cortes.
- [x] 5.5 **REFACTOR**: Limpiar código y verificar que `Dialog.test.tsx` y los tests de modales de appointments siguen 100% en verde e intactos.

## 6. Verificación de Código, Tooling y Mutaciones

- [x] 6.1 Ejecutar `npm run build` o `npx tsc --noEmit` y verificar código de salida 0.
- [x] 6.2 Ejecutar `npm run lint` y verificar código de salida 0 (3 advertencias preexistentes documentadas).
- [x] 6.3 Ejecutar la suite completa de pruebas unitarias (`npx vitest run`) y verificar que todos los tests pasan en verde (260 anteriores + 12 nuevos = 272 tests).
- [x] 6.4 Implementar y ejecutar script de análisis de mutaciones `docs/evidencias/mutaciones-C-36.py` verificando 12/12 mutaciones eliminadas con 0 supervivientes y 0 mutaciones inválidas.
- [x] 6.5 Corrección grilla: cálculo de ancho útil de columna mediante container query `100cqi` sin `100vw` en `AgendaGrid.module.css` (test 09, M09).
- [x] 6.6 Corrección toolbar: estructuración estricta en 3 filas con botones Anterior/Siguiente ('‹'/'›') y Actualizar ('↻') con nombre accesible intacto y `flex-wrap: nowrap` en navRow (test 10, M10).
- [x] 6.7 Corrección espaciado: reducción de separación entre título y toolbar en `PageShell.module.css` y adición de margen superior a fecha en `AgendaView.module.css` (test 11, M11).
- [x] 6.8 Corrección sticky eje de horas: asignación de `z-index: 5` y background de superficie a `timeGutter` y `z-index: 6` a `cornerCell` en móvil para evitar que tarjetas pasen por encima al deslizar (test 12, M12).

## 7. Verificación Visual Multi-Resolución a cargo de Claude

- [ ] 7.1 Tomar capturas reales a 1440 px, 768 px y 390 px de `AppShell` y Menú móvil desplegado.
- [ ] 7.2 Tomar capturas reales a 1440 px, 768 px y 390 px de `AgendaToolbar` compacta y panel de filtros.
- [ ] 7.3 Tomar capturas reales a 1440 px, 768 px y 390 px de `AgendaGrid` con scroll-snap en vista diaria y semanal.
- [ ] 7.4 Tomar capturas reales a 1440 px, 768 px y 390 px de los modales de turnos como hoja inferior sin botones cortados.
- [ ] 7.5 Consolidar informe de verificación en `docs/evidencias/verify-C-36.md`.

---

## Tabla de Trazabilidad: Escenario → Test → Mutación

| # | Spec | Requisito | Escenario | Tipo | Archivo de Test | Mutación Asociada |
|---|---|---|---|---|---|---|
| 1 | `frontend-foundation` | AppShell en celular con botón Menú | Cabecera compacta y apertura de menú en celular | Testeable | `AppShell.mobile.test.tsx` | M01: Omitir botón Menú o atributo `aria-controls` en móvil |
| 2 | `frontend-foundation` | AppShell en celular con botón Menú | Cierre del menú con Escape y retorno de foco al botón | Testeable | `AppShell.mobile.test.tsx` | M02: No retornar el foco al botón Menú al presionar Escape |
| 3 | `frontend-foundation` | AppShell en celular con botón Menú | Navegación de AppShell y menú verificados a 1440, 768 y 390 px | Visual | Capturas 1440 / 768 / 390 px | V01: Desborde o rotura de cabecera en captura real |
| 4 | `frontend-foundation` | Modales como hoja inferior en celular | Hoja inferior a ancho completo con scroll interno en celular | Testeable | `Dialog.bottomSheet.test.tsx` | M03: Omitir clase o estilo de hoja inferior en <= 640 px |
| 5 | `frontend-foundation` | Modales como hoja inferior en celular | Preservación de modal centrado flotante en tablet y escritorio | Testeable | `Dialog.bottomSheet.test.tsx` | M04: Aplicar hoja inferior en pantallas >= 768 px |
| 6 | `frontend-foundation` | Modales como hoja inferior en celular | Modales de turnos verificados a 1440, 768 y 390 px | Visual | Capturas 1440 / 768 / 390 px | V02: Botones cortados en borde inferior de pantalla móvil |
| 7 | `frontend-agenda` | Toolbar de agenda compacta con filtros plegables | Organización compacta de navegación y fecha en celular | Testeable | `AgendaToolbar.mobile.test.tsx` | M05: Mantener controles en fila única sin distribución en 2 filas |
| 8 | `frontend-agenda` | Toolbar de agenda compacta con filtros plegables | Botón Filtros con contador de filtros activos y panel accesible | Testeable | `AgendaToolbar.mobile.test.tsx` | M06: Omitir contador de filtros activos en el botón Filtros |
| 9 | `frontend-agenda` | Toolbar de agenda compacta con filtros plegables | Toolbar de agenda verificada a 1440, 768 y 390 px | Visual | Capturas 1440 / 768 / 390 px | V03: Altura de toolbar > 110 px en captura de 390 px |
| 10 | `frontend-agenda` | Grilla de agenda con scroll-snap y columna completa | Desplazamiento horizontal fluido con scroll-snap y horas fijas | Testeable | `AgendaGrid.mobile.test.tsx` | M07: Omitir `scroll-snap-type` en contenedor de grilla |
| 11 | `frontend-agenda` | Grilla de agenda con scroll-snap y columna completa | Columna completa al ancho útil y preservación de grilla por defecto | Testeable | `AgendaGrid.mobile.test.tsx` | M08: Cambiar el modo por defecto de `AgendaView` a lista |
| 12 | `frontend-agenda` | Grilla de agenda con scroll-snap y columna completa | Grilla de agenda verificada a 1440, 768 y 390 px | Visual | Capturas 1440 / 768 / 390 px | V04: Columna recortada o ilegible en captura de 390 px |

---

## Workflow Follow-up

- Actualizar la descripción de `[C-36]` en `CHANGES.md` al archivar el change para reflejar el reenfoque en celular de la app y el traslado del tema oscuro de la app al backlog.
- Archivar el change mediante `/opsx:archive ui-tema-oscuro-y-movil`.
- Sincronizar las delta specs hacia las specs principales en `openspec/specs/`.
