# Tasks

## 1. Safety Net y Funciones Puras de Tiempo

- [ ] 1.1 Ejecutar la suite de tests existente y verificar que los 127 tests de C-27 pasan sin modificaciones
- [ ] 1.2 Escribir tests unitarios que fallen (RED) para `weekRangeOf` y `getWeekDates` en `agendaTime.test.ts` cubriendo semana lunes-domingo, cruce de fin de mes y cruce de fin de año, y guardar la evidencia en `docs/evidencias/red-C-28/red-agendaTime.txt`
- [ ] 1.3 Implementar `weekRangeOf` y funciones auxiliares de semana en `agendaTime.ts` y verificar que los tests pasen (GREEN)
- [ ] 1.4 Aplicar mutaciones en el cálculo de rango de semana (desfasaje de inicio, fin de semana erróneo) y verificar que los tests las detectan con el detector de mutaciones

## 2. Abstracción de Layout y Hook de Agenda

- [ ] 2.1 Escribir tests unitarios que fallen (RED) en `agendaLayout.test.ts` para `groupByDayForProfessional` cubriendo 7 columnas de lunes a domingo, distribución de turnos por día local según timezone, horarios del día y bloqueos, y guardar evidencia en `docs/evidencias/red-C-28/red-agendaLayout.txt`
- [ ] 2.2 Implementar `groupByDayForProfessional` en `agendaLayout.ts` reutilizando `assignLanes` y `computeAxis`, y verificar que los tests pasen (GREEN)
- [ ] 2.3 Escribir tests que fallen (RED) en `useAgenda.test.tsx` para la carga semanal con `from` y `to` de 7 días, verificando que la semana se pide en exactamente una sola llamada a `GET /api/agenda`, y guardar evidencia en `docs/evidencias/red-C-28/red-useAgenda.txt`
- [ ] 2.4 Extender `useAgenda.ts` para admitir rango semanal en una sola llamada a `fetchAgenda` conservando la retrocompatibilidad diaria, y verificar que los tests pasen (GREEN)
- [ ] 2.5 Aplicar mutaciones sobre el rango de fechas pedido y el conteo de llamadas HTTP, verificando que los tests las detectan

## 3. Toolbar y Navegación Semanal

- [ ] 3.1 Escribir tests de componentes que fallen (RED) en `AgendaToolbar.test.tsx` para:
  - Control `[ Día | Semana ]` y alternancia de día a semana conservando fecha y filtros
  - Alternancia de semana a día conservando el día exacto de anclaje y filtros
  - Botones "Semana anterior" / "Semana siguiente" con salto de `+/- 7` días que cruza mes y año
  - Botón "Hoy" en vista semanal saltando a la semana actual del `Clock`
  y guardar evidencia en `docs/evidencias/red-C-28/red-AgendaToolbar.txt`
- [ ] 3.2 Implementar el control segmentado de vista y las etiquetas dinámicas de navegación en `AgendaToolbar.tsx` y verificar que los tests pasen (GREEN)
- [ ] 3.3 Aplicar mutaciones sobre la alternancia de vistas en ambas direcciones y las etiquetas de navegación semanal, verificando que los tests las matan

## 4. Integración de la Vista Semanal y AgendaPage

- [ ] 4.1 Escribir tests de componentes que fallen (RED) en `AgendaView.test.tsx` y `AgendaPage.test.tsx` para:
  - Renderizado de 7 columnas de lunes a domingo con turno en el día local correcto según `timezone`
  - Preselección automática por rol odontólogo a su propio id
  - Preselección automática por rol recepción/administrador a "Dr. Martín Sosa" (primer profesional activo en el orden de `compareProfessionals`)
  - Turno cancelado visible con texto "Cancelado"
  - Marca visible "Hoy" en cabecera con atributo `aria-current="date"`
  - Semana vacía sin turnos con grilla visible y aviso "No hay turnos esta semana para [profesional]"
  - Semana vacía con filtro de sillón activo mostrando "Sin turnos para este filtro" y no el aviso de profesional
  - Fallback de `view` desconocido o ausente a vista diaria
  - Verificación estática de CSS en `agendaStyles.test.ts` de `overflow-x: auto` en contenedor y columna de horas sticky para tablet
  y guardar la evidencia en `docs/evidencias/red-C-28/red-AgendaPage.txt`
- [ ] 4.2 Implementar la integración de la vista semanal en `AgendaGrid.tsx`, `AgendaView.tsx` y `AgendaPage.tsx`, y verificar que todos los tests pasen (GREEN)
- [ ] 4.3 Aplicar mutaciones sobre la preselección por rol, la visualización de avisos de vacío y el atributo `aria-current="date"`, verificando que los tests las detectan
- [ ] 4.4 Ejecutar la suite completa y verificar que los 127 tests originales de C-27 más todos los nuevos tests de C-28 pasen limpiamente sin ninguna regresión

## 5. Mutaciones, Trazabilidad, Evidencias y Documentación

- [ ] 5.1 Ejecutar el detector de mutaciones inválidas sobre los tests nuevos de C-28 y generar el reporte en `docs/evidencias/mutaciones-C-28.txt`
- [ ] 5.2 Generar el script de trazabilidad de escenarios de C-28 contrastando la spec delta contra los tests y registrar `docs/evidencias/trazabilidad-C-28.txt`
- [ ] 5.3 Tomar capturas de verificación visual en escritorio (1440 px) y tablet (768 px) de la vista semanal y guardarlas en `docs/evidencias/capturas/`
- [ ] 5.4 Completar la sección "5. Uso en C-28" en `docs/skills-mcp/aplicacion.md` documentando la aplicación de la skill `appointment-frontend-ux` y la evidencia 04 de Context7
- [ ] 5.5 Redactar el informe de verificación `docs/evidencias/verify-C-28.md` y comprobar que `openspec validate --all --strict` valide en verde
