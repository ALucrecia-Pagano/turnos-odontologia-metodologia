# Visión y Objetivos

> Fuente: `docs/discovery/informe-discovery.md` y `docs/discovery/checklist-discovery.md` (Discovery confirmado por la autora el 2026-10-03). Cuando una decisión no figura en esas fuentes se marca como **Suposición:**.

## Propósito del sistema

**turnos-odontologia** es un sistema web de gestión de turnos y agenda para consultorios odontológicos pequeños de Argentina, cuyo núcleo es una **agenda sin conflictos**: el sistema rechaza, desde la lógica de dominio y con un motivo explícito, todo turno que se superponga con otro del mismo profesional o del mismo sillón, que caiga fuera del horario de atención o dentro de un bloqueo, o que esté en el pasado.

**Problema.** Los consultorios con 2 a 5 profesionales, varios sillones y secretaria o recepción suelen administrar la agenda en papel, planillas o WhatsApp. Ese método produce solapamientos de profesionales y de sillones y desordena la operación diaria.

**Oportunidad detectada.** El relevamiento de 26 sistemas (solo fuentes públicas) no encontró ninguno que *compruebe* un rechazo estricto de solapamientos por profesional y por sillón específico (Open Dental lo impide por operatorio salvo configuración; Odonthia avisa pero permite forzar el sobreturno). "No evidenciado" no significa "no existe": es falta de evidencia pública, no prueba de ausencia (riesgo 4 del checklist).

## Objetivos por actor

| Actor | Objetivo principal | Objetivos secundarios | Alcance |
|-------|--------------------|-----------------------|---------|
| Secretaria / recepción | Dar, mover y cancelar turnos de todos los profesionales sin generar conflictos | Ver agenda diaria/semanal por profesional y por sillón; marcar estados | MVP |
| Odontólogo | Consultar su agenda y gestionar sus horarios y bloqueos | Marcar turnos como confirmado, atendido o ausente | MVP |
| Administrador / dueño | Configurar consultorio, profesionales, sillones y prestaciones (con duración) | Mantener el catálogo y los horarios | MVP |
| Paciente | Autogestión de turnos (reservar, confirmar, cancelar, reprogramar) | — | Posterior al MVP |

## Alcance v0.1 (MVP)

- Crear un turno sin solapamientos por profesional ni por sillón, con mensajes de conflicto que indican qué turno o bloqueo choca (**C-02, solo lógica de dominio**: solapamiento por profesional y por sillón, duración por prestación (rechazando duración no positiva) y turnos consecutivos; sin horarios, bloqueos ni el resto de las validaciones, que van en C-03 a C-08).
- Horario de atención por profesional y bloqueos (vacaciones, feriados, ausencias).
- Catálogo de prestaciones con duración por defecto, editable al dar el turno.
- Ciclo de vida del turno: cancelar y reprogramar; estados `reservado`, `confirmado`, `atendido`, `ausente`, `cancelado`; transiciones válidas explícitas.
- Historial de cambios de estado del turno (quién, cuándo, de qué estado a cuál).
- Datos mínimos y **ficticios** del paciente: nombre, DNI, teléfono, obra social como texto.
- Tres roles: odontólogo, recepción, administrador.
- Interfaz web con vistas diaria y semanal por profesional y por sillón, y vista de recepción por sillón (C-22 a C-29, posteriores al dominio y la API; frontend cuidado).
- Diferenciadores: mensajes de rechazo explicativos y vista de recepción por sillón.

## Fuera de alcance (MVP)

- Sobreturnos (prohibidos: todo solapamiento se rechaza).
- Regla de paciente sin turnos simultáneos (diferida; el modelo debe permitir agregarla).
- Búsqueda del primer hueco disponible.
- Integraciones externas: WhatsApp (enlace y API), Google Calendar, Mercado Pago, ARCA, obras sociales.
- Reserva online del paciente, lista de espera, seña/cobros, facturación.
- Ficha clínica y odontograma (no se almacena información clínica).
- Múltiples sedes, reportes y exportación de datos.
- Datos reales de pacientes (**nunca**: solo datos ficticios).

## Métricas de éxito

Orientadas a la entrega académica (trabajo individual). Hay un avance el 2026-10-08 sin contenido exigido definido; la **entrega final** es la semana siguiente (fecha **a confirmar**). Las métricas rigen para la entrega final:

| Métrica | Criterio |
|---------|----------|
| Cobertura de escenarios | Cada escenario del spec tiene al menos un test automatizado (Vitest, Strict TDD) |
| Integridad de agenda | Ninguna combinación de entradas válidas produce dos turnos activos solapados para un mismo profesional o sillón |
| Claridad de rechazo | Todo rechazo devuelve un código estable y un mensaje en español que identifica el turno o bloqueo en conflicto |
| C-02 terminable | El change de dominio puro (C-02, sobre la base de C-01) queda completo y verde antes de empezar la interfaz |
| Higiene del repo | Sin credenciales ni datos reales en el repositorio |

## Restricciones relevantes

Avance el 2026-10-08 sin contenido exigido definido; entrega final la semana siguiente (fecha a confirmar) · trabajo individual · tests para cada escenario del spec · solo datos ficticios · sin credenciales en el repo · C-02 chico (dominio puro) y UI en changes posteriores (C-22 a C-29) · interfaz web con frontend cuidado. Detalle de riesgos en [10_preguntas_abiertas.md](10_preguntas_abiertas.md).
