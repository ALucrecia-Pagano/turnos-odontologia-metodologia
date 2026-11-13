# Design

## Context

C-27 y C-28 consolidaron la agenda médica diaria y semanal en `frontend/src/features/agenda/`, y C-29 proveyó la primitiva modal accesible `frontend/src/shared/components/Dialog.tsx` junto con el formulario de alta de turnos `AppointmentFormDialog.tsx`. El backend implementó en C-23 (`backend/app/api/appointments.py`) los endpoints de ciclo de vida del turno (`/{id}/status`, `/{id}/cancel`, `/{id}/reschedule`, `/{id}/history`), respaldados por el dominio puro en `backend/app/domain/appointment/transitions.py` y `reschedule.py`, y la matriz de seguridad RBAC en `backend/app/auth/permissions.py`.

Este diseño define la arquitectura de interfaz para operar estos endpoints desde la agenda, preservando la regla C1 de tests, la integridad de los tests existentes y los lineamientos de accesibilidad y diseño del proyecto.

## Goals / Non-Goals

**Goals:**
- Turnos interactivos y accesibles en `AgendaGrid` como `<button type="button">` y botón "Ver turno" en `AgendaTable`.
- Diálogo modal de detalle `AppointmentDetailDialog` con datos en hora local e indicador de estado `StatusBadge`.
- Panel cronológico de historial que detalla transiciones, autores y cambios de intervalo en hora local.
- Botones de acción contextuales según estado y rol, sin lógica temporal en el cliente.
- Cancelación protegida con confirmación interna in-dialog (sin `window.confirm`).
- Diálogo de reprogramación `AppointmentRescheduleDialog` con paciente y prestación en solo lectura y revalidación de solapamiento en el dominio.
- Anuncios accesibles mediante la región permanente con `role="status"` en `AgendaPage`.
- Cero regresiones en la suite existente de 191 tests.

**Non-Goals:**
- Crear pacientes, prestaciones o turnos nuevos desde este flujo (resuelto en C-29).
- Modificar la regla de "Turnos" en el menú principal (`menuFor.ts` continúa en "Próximamente").
- Replicar validaciones dinámicas temporales o de agenda en el cliente (el dominio en Python es la única autoridad).

---

## Análisis de Tests Existentes de la Agenda (Garantía de no regresión)

Se realizó un análisis exhaustivo del código de pruebas existente para asegurar que la incorporación de interactividad en `AgendaGrid` y `AgendaTable` no rompa ningún test preexistente:

### 1. `AgendaGrid.tsx` en `AgendaView.test.tsx` y `AgendaPage.test.tsx`
- **Cómo consultan los tests hoy**: Los tests de `AgendaView.test.tsx` (líneas 161, 231, 302, 332, etc.) y `AgendaPage.test.tsx` (líneas 193, 225, 276, 323, etc.) localizan las tarjetas de turno exclusivamente mediante `screen.queryByTestId("agenda-appointment-<uuid>")` o `within(col).queryByTestId(...)`.
- **Aserciones sobre la tarjeta**: Verifican atributos `data-lane`, `data-lane-count`, `data-status`, la clase CSS `.appointmentCancelled`, el estilo porcentual (`top`, `height`, `left`, `width`) y el texto visible del estado mediante `toHaveTextContent("Cancelado")`.
- **Inexistencia de dependencias de tag**: Ningún test en el repositorio verifica `card.tagName === "ARTICLE"`, ni consulta `getByRole("article")`.
- **Inexistencia de colisiones con `getByRole("button")`**: Las consultas de botones en los tests existentes siempre filtran explícitamente por nombre accesible (`{ name: "Semana" }`, `{ name: "Día" }`, `{ name: "Hoy" }`, `{ name: "Ver como lista" }`). Ningún test de agenda llama a `getAllByRole("button")` globalmente sin discriminación.
- **Conclusión para `AgendaGrid`**: Transformar el elemento contenedor `<article>` directamente en un `<button type="button">` conservando idénticas clases, estilos y atributos `data-*` y `aria-label` **no rompe ningún test existente**.

### 2. `AgendaTable.tsx` en `AgendaTable.test.tsx` y `AgendaView.test.tsx`
- **Cómo consultan los tests hoy**:
  - `AgendaTable.test.tsx` (líneas 52-60) y `AgendaView.test.tsx` (líneas 588-596) verifican taxativamente que la lista de encabezados coincida de forma exacta:
    `expect(headers).toEqual(["Hora", "Paciente", "Profesional", "Sillón", "Prestación", "Estado"])`.
  - Asimismo, `AgendaTable.test.tsx` (líneas 68-86) y `AgendaView.test.tsx` (líneas 600-608) mapean las celdas de las filas (`within(row).queryAllByRole("cell").map(td => td.textContent)`) y esperan exactamente 6 elementos de texto sin columnas adicionales.
- **Riesgo identificado**: Si `AgendaTable` agregara incondicionalmente una 7ª columna `<th scope="col">Acción</th>` o incrustara el botón "Ver turno" dentro de una celda de texto existente, **ambos tests existentes fallarían de inmediato**.
- **Solución arquitectónica**: La prop `onSelectAppointment` se declara opcional en `AgendaTableProps` (`onSelectAppointment?: (appointment: AgendaAppointment) => void`).
  - Cuando `onSelectAppointment` **no** se provee (caso de `AgendaTable.test.tsx` y `AgendaView.test.tsx`), la tabla renderiza con exactitud los 6 encabezados y las 6 celdas de datos habituales.
  - Cuando `onSelectAppointment` **sí** se provee (al conectarse desde `AgendaPage` en el nuevo flujo de C-30), se renderiza la columna adicional con el botón accesible `<button type="button">Ver turno</button>` por fila.
- **Conclusión para `AgendaTable`**: Se garantiza compatibilidad regresiva del 100% con los tests existentes mientras se habilita la nueva funcionalidad.

---

## Decisions

### D1 — Ubicación en `AppointmentDetailDialog` con `Dialog.tsx`
El detalle de las acciones vive en el componente modal `frontend/src/features/appointments/AppointmentDetailDialog.tsx`, que envuelve la primitiva accesible `Dialog.tsx` de C-29. Se abre al activar cualquier turno desde `AgendaGrid` o `AgendaTable` y traslada el foco al diálogo. Al cerrarse, el foco retorna al turno disparador.

*Alternativa descartada:* Menús desplegables directos sobre la tarjeta, que provocan desbordes críticos en tarjetas angostas o carriles divididos.

### D2 — Formulario dedicado `AppointmentRescheduleDialog.tsx`
Se crea un componente modal separado para la reprogramación. A diferencia del alta, el backend exige que el paciente y la prestación permanezcan inalterables; el formulario los muestra como texto de solo lectura. Los únicos controles editables son fecha (`input type="date"`), hora (`input type="time" step="300"`), selector de profesional, selector de sillón y duración (`input type="number" step="5" min="5" max="480"`). Reutiliza la función pura `buildStartAtIso` y la primitiva `Dialog.tsx`.

*Alternativa descartada:* Agregar modos condicionales a `AppointmentFormDialog.tsx`, lo que añadiría complejidad innecesaria a un componente probado.

### D3 — Cancelación con confirmación in-dialog
Al presionar "Cancelar turno", el modal de detalle pasa a un estado de confirmación interno ("¿Confirma que desea cancelar el turno de [Paciente]?") que presenta un botón destructivo "Confirmar cancelación" y un botón secundario "Volver al detalle". No se solicita motivo porque la API `POST /{id}/cancel` no recibe cuerpo.

*Alternativa descartada:* `window.confirm()`, prohibido por accesibilidad y por la regla C1 (requiere stubs globales).

### D4 — Botones de acción y etiquetas según estado y rol
Sin lógica horaria en el cliente (la guarda de tiempo pertenece al dominio).
- **Etiquetas exactas**:
  - Acciones: `"Confirmar turno"`, `"Marcar atendido"`, `"Marcar ausente"`, `"Reprogramar"`, `"Cancelar turno"`.
  - Estados (copiados de `StatusBadge.tsx`): `"Reservado"`, `"Confirmado"`, `"Atendido"`, `"Ausente"`, `"Cancelado"`.
- **Botones por estado**:
  - En `reservado`: Confirmar turno, Marcar atendido, Marcar ausente, Reprogramar, Cancelar turno.
  - En `confirmado`: Marcar atendido, Marcar ausente, Reprogramar, Cancelar turno.
  - En `atendido`, `ausente`, `cancelado`: Ningún botón de mutación; se muestra el texto accesible: `"Este turno ya no admite cambios."`.
- **Manejo de rechazos 409 y 422**: Si el usuario intenta marcar atendido antes del inicio, la API devuelve `422 STATUS_CHANGE_TOO_EARLY`. El diálogo captura la respuesta y expone en el contenedor superior de alertas con `role="alert"` el código y mensaje textual del dominio, trasladando el foco al alert.

### D5 — Visualización cronológica del historial
Sección integrada en el detalle que consulta `GET /api/appointments/{id}/history`. Despliega cada evento en orden cronológico mostrando autor (`changedByName`), transición (`from → to`), y fecha/hora formateada en hora local con la `timezone` de la agenda. Si la entrada posee `reschedule`, muestra el desglose del intervalo previo y nuevo en hora local.

### D6 — Anuncios accesibles en la región permanente de `AgendaPage`
Tras completar cualquier mutación exitosamente:
1. Se cierra el modal.
2. Se ejecuta `useAgenda().refresh()`.
3. Se actualiza `statusMessage` en `AgendaPage.tsx` para emitir el anuncio textual en la región permanente con `role="status"` y `aria-live="polite"`:
   - Confirmar: `"Turno confirmado."`
   - Atendido: `"Turno marcado como atendido."`
   - Ausente: `"Turno marcado como ausente."`
   - Cancelar: `"Turno cancelado."`
   - Reprogramar: `"Turno reprogramado para el DD/MM/AAAA a las HH:MM."`

### D7 — Control de acceso estricto para el rol Odontólogo
- **Turnos propios** (`user.professionalId === appointment.professionalId`): Habilita los botones de cambio de estado ("Confirmar turno", "Marcar atendido", "Marcar ausente") y permite consultar el historial. Oculta los botones "Reprogramar" y "Cancelar turno" (la API devolvería 403 `FORBIDDEN_OPERATION`).
- **Turnos ajenos**: Vista estrictamente de solo lectura; sin botones de mutación y sin disparar la consulta a `GET /api/appointments/{id}/history` (evitando un 403 evitable).

### D8 — Marcado accesible en la agenda
- `AgendaGrid`: Cada turno es un `<button type="button">` real con `aria-label` exhaustivo (`"{hora}, {paciente}, {prestación}, {profesional}, {sillón}, {estado}"`). No se fuerza un `min-height: 44px` en la tarjeta para no alterar la escala porcentual continua de la grilla. El foco visible se realiza mediante `outline: 2px solid var(--color-focus)`.
- `AgendaTable`: Botón accesible `"Ver turno"` en cada fila cuando la prop `onSelectAppointment` está presente.

### D9 — Menú principal ("Turnos") permanece en "Próximamente"
El ítem "Turnos" en `frontend/src/features/auth/menuFor.ts` se mantiene deshabilitado con `badge: "Próximamente"`, garantizando que `menuFor.test.ts` y `AppShell.test.tsx` permanezcan intactos.

### D10 — Regla de un solo botón primario por vista
En cada modal, únicamente la acción principal de avance ostenta la clase `primaryButton` (ej. "Confirmar turno" o "Guardar reprogramación"). Las demás acciones adoptan `secondaryButton`, y "Cancelar turno" o "Confirmar cancelación" adoptan `dangerButton`.

---

## Contratos reales de la API (`backend/app/api/appointments.py`)

### 1. `GET /api/appointments/{id}`
- **Respuesta 200 OK (`AgendaAppointmentResponse`)**:
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "patientId": "00000000-0000-0000-0000-0000000000c1",
  "patientName": "Ana Pérez",
  "professionalId": "00000000-0000-0000-0000-000000000001",
  "professionalName": "Dra. Laura Quiroga",
  "chairId": "00000000-0000-0000-0000-0000000000b1",
  "chairName": "Sillón 1",
  "serviceId": "00000000-0000-0000-0000-0000000000d1",
  "serviceName": "Consulta general",
  "startAt": "2026-11-16T13:00:00Z",
  "endAt": "2026-11-16T13:30:00Z",
  "status": "reservado"
}
```

### 2. `POST /api/appointments/{id}/status`
- **Cuerpo (`StatusChangeInput`, `extra="forbid"`)**:
```json
{
  "toStatus": "confirmado"
}
```
*(Valores permitidos: `"confirmado"`, `"atendido"`, `"ausente"`; `"cancelado"` da 400).*
- **Respuesta 200 OK (`AppointmentResponse`)**: Devuelve el turno con `status: "confirmado"`.

### 3. `POST /api/appointments/{id}/cancel`
- **Cuerpo**: Vacío.
- **Respuesta 200 OK (`AppointmentResponse`)**: Devuelve el turno con `status: "cancelado"`.

### 4. `POST /api/appointments/{id}/reschedule`
- **Cuerpo (`RescheduleInput`, `extra="forbid"`)**:
```json
{
  "startAt": "2026-11-17T14:00:00-03:00",
  "professionalId": "00000000-0000-0000-0000-000000000001",
  "chairId": "00000000-0000-0000-0000-0000000000b1",
  "durationMin": 45
}
```
- **Respuesta 200 OK (`AppointmentResponse`)**: Devuelve el turno actualizado con `status: "reservado"`.

### 5. `GET /api/appointments/{id}/history`
- **Respuesta 200 OK (`list[HistoryEntryResponse]`)**:
```json
[
  {
    "from": null,
    "to": "reservado",
    "changedBy": "00000000-0000-0000-0000-000000000002",
    "changedByName": "Recepción",
    "changedAt": "2026-11-13T10:00:00Z",
    "reschedule": null
  },
  {
    "from": "reservado",
    "to": "reservado",
    "changedBy": "00000000-0000-0000-0000-000000000002",
    "changedByName": "Recepción",
    "changedAt": "2026-11-13T11:00:00Z",
    "reschedule": {
      "previousStartAt": "2026-11-16T13:00:00Z",
      "previousEndAt": "2026-11-16T13:30:00Z",
      "newStartAt": "2026-11-17T14:00:00Z",
      "newEndAt": "2026-11-17T14:45:00Z",
      "previousProfessionalId": "00000000-0000-0000-0000-000000000001",
      "newProfessionalId": "00000000-0000-0000-0000-000000000001",
      "previousChairId": "00000000-0000-0000-0000-0000000000b1",
      "newChairId": "00000000-0000-0000-0000-0000000000b1"
    }
  }
]
```

---

## Risks / Trade-offs

- **[Riesgo de discrepancia horaria cliente-servidor]** → *Mitigación*: El cliente no realiza validaciones bloqueantes de tiempo (como `now >= start_at`); delega en el backend y presenta el rechazo `STATUS_CHANGE_TOO_EARLY` tal cual en el alert accesible.
- **[Riesgo de colisión en tests de `AgendaTable`]** → *Mitigación*: `onSelectAppointment` se declara opcional; cuando no se provee, la tabla renderiza las 6 columnas originales exactas que esperan los tests existentes.
- **[Riesgo de layout roto en jsdom]** → *Mitigación*: Todas las aserciones de pruebas de componentes se basan en accesibilidad (roles, textos, labels y atributos nativos); los aspectos cosméticos (centrado modal, desbordes a 390 px) se verifican mediante capturas visuales independientes con navegador real.
