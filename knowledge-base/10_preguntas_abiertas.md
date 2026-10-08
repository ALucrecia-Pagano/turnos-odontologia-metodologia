# Preguntas Abiertas

Ninguna bloquea C-02 (dominio puro de crear turno; C-01 es su prerrequisito técnico), salvo donde se indica. Las preguntas Q-01 a Q-07 vienen del checklist §11; para cada una el MVP propone un default marcado **Suposición:** (ver [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md)).

## Inconsistencias detectadas

### IN-01 — Puntaje de Odonthia desactualizado en el estado compartido (RESUELTA)
**Estado:** resuelta el 2026-10-07: se actualizó `discovery.competitors[0].score` de 3.5 a 3.25 en `.active-orchestrator-state.json`.
**Documento A dice** (`.active-orchestrator-state.json`, `discovery.competitors[0].score`): 3.5.
**Documento B dice** (`docs/discovery/informe-discovery.md`, B.2 y B.3): 3,25 (la nota T bajó de 5 a 4 tras la verificación manual del 2026-10-06).
**Impacto**: bajo; solo afecta la referencia al ranking. La KB usa 3,25 (informe).
**Resolución**: el campo en el estado se actualizó a 3.25 el 2026-10-07; ya no hay discrepancia con el informe.

### IN-02 — Restricción "sin contactar proveedores" ausente en el estado
**Documento A dice** (estado, `discovery.restricciones`): lista siete restricciones.
**Documento B dice** (checklist §9): agrega "Sin contactar proveedores ni crear cuentas" (consigna de investigación).
**Impacto**: nulo para el producto (aplica a la investigación, no al sistema).
**Resolución propuesta**: ignorar para la KB; opcionalmente sincronizar el estado.

### IN-03 — Estricto vs. flexible frente al uso real
**Documento A dice** (checklist §7): sobreturnos prohibidos y turnos fuera de horario rechazados.
**Documento B dice** (checklist riesgo 9 e informe D.3): el competidor mejor documentado (Odonthia) avisa y permite forzar ("Agendar igual"); una urgencia fuera de horario es legítima.
**Impacto**: el MVP puede resultar demasiado rígido en uso real.
**Resolución propuesta**: mantener estricto en el MVP (decisión de la autora) y modelar las reglas como componibles para habilitar sobreturnos/forzado con autorización en un change posterior (ver RN-AG-03).

### IN-04 — Stack anterior fuera de la knowledge-base (PARCIALMENTE RESUELTA)
**Estado:** `CHANGES.md` se regeneró el 2026-10-08 con el stack de la cátedra (33 changes; C-01 pasó a `fundacion-backend-y-dominio`). Quedan pendientes los demás archivos.
**Documento A dice** (esta KB y `CHANGES.md`, desde el 2026-10-08): stack de la cátedra (Python + FastAPI + JWT + SQLAlchemy + PostgreSQL + Redis + Docker Compose; React + TypeScript + Vite).
**Documento B dice** (`CLAUDE.md`, `AGENTS.md`, `.atl/skill-registry.md` y el estado compartido): stack TypeScript full-stack (Fastify, SQLite, workspaces de npm, rol simulado), numeración vieja de los changes de persistencia, API y UI, y 29 changes.
**Impacto**: alto para los agentes: leen `CLAUDE.md`/`AGENTS.md` primero y aplicarían el stack viejo (por ejemplo, la regla dura de `packages/domain` y las skills de TS). No afecta las reglas de negocio ni los escenarios de C-02.
**Resolución propuesta**: regenerar `CLAUDE.md`/`AGENTS.md` (agent-instruction) y el registro de skills a partir de esta KB y de `CHANGES.md`, en un paso aparte y **antes** del `/opsx:propose` de C-01.

## Preguntas abiertas (priorizadas)

| ID | Prioridad | Pregunta | Default propuesto en el MVP | Bloquea | Decisor |
|----|-----------|----------|-----------------------------|---------|---------|
| Q-06 | Alta | ¿Zona horaria y granularidad de horario? | **Suposición:** `America/Argentina/Buenos_Aires`; 5 min; duración 5–480 min (SU-01, SU-02) | C-04 (la zona horaria) y C-03 (granularidad de 5 min, Q-13) | Autora |
| Q-03 | Alta | ¿Qué transiciones de estado son válidas (reprogramar atendido, reactivar cancelado)? | **Suposición:** tabla de RN-TU-02; terminales atendido/ausente/cancelado (SU-03) | C-10 (transiciones de estado) | Autora |
| Q-04 | Alta | ¿Qué pasa con los turnos existentes al crear un bloqueo que los pisa? | **Suposición:** no se cancelan; se informan para reprogramar (SU-05) | C-06 (bloqueos de agenda) | Autora |
| Q-05 | Media | ¿Algunas prestaciones exigen un sillón específico? | **Suposición:** no; cualquier prestación en cualquier sillón (SU-04) | C-09 (catálogo) | Autora |
| Q-01 | Media | ¿Anticipación mínima para cancelar (p. ej. 24 h)? | **Suposición:** sin mínimo (SU-08) | C-10 | Autora |
| Q-02 | Media | ¿Se puede marcar "ausente" antes de la hora de inicio? | **Suposición:** no; solo con `now >= inicio` (SU-08) | C-10 | Autora |
| Q-07 | Cerrada | ¿Stack de implementación? | **Resuelta por la cátedra (2026-10-08):** backend Python + FastAPI + JWT + SQLAlchemy + PostgreSQL + Redis, Docker Compose; frontend React + TypeScript + Vite (DD-01). Reemplaza la respuesta anterior (TypeScript full-stack, DD-01 v1) | — | Cátedra |
| Q-08 | Media | ¿Qué estados ocupan agenda (¿`ausente` libera el hueco?) | **Suposición:** reservado/confirmado/atendido ocupan (SU-07) | C-02 (la regla de solapamiento depende de esto) | Autora |
| Q-09 | Cerrada | ¿Hace falta autenticación real en la entrega? | **Resuelta por la cátedra (2026-10-08):** sí, con JWT y los tres roles (DD-11). Queda abierto solo su alcance: sin refresh tokens ni revocación (**Suposición**, SU-06) | C-19 (autenticación JWT) y C-26 (login en la web) | Cátedra |
| Q-14 | Media | ¿La cátedra espera algún uso concreto de Redis en la entrega? | **Suposición:** no; el MVP no tiene funcionalidades asincrónicas y Redis queda levantado sin uso (DD-10, SU-11) | C-13 (servicio en Compose); ningún change de dominio | Cátedra |
| Q-10 | Media | ¿El odontólogo puede dar turnos nuevos o solo recepción/administrador? | **Suposición:** solo recepción y administrador (ver 03) | C-19 (matriz RBAC) y C-22 (API dar turno) | Autora |
| Q-11 | Baja | Al reprogramar, ¿el turno vuelve a `reservado` o conserva `confirmado`? | **Suposición:** vuelve a `reservado` (RN-TU-03) | C-11 (reprogramar turno) | Autora |
| Q-12 | Baja | ¿Se admiten turnos que cruzan medianoche? | **Suposición:** no (RN-AG-10) | C-04 (turno en un día, Q-13) | Autora |
| Q-13 | Cerrada | **Resuelta el 2026-10-07.** ¿Qué otras reglas entran en C-02 además de solapamientos, duración y turnos consecutivos? Candidatas (no incluidas, DD-09): no en el pasado (US-005), validación de duración y granularidad (US-007 CA-1), existencia/estado de profesional, sillón y prestación (US-007 CA-2), turno que cruza medianoche (US-007 CA-3), contrato de errores con mensajes y códigos completos (US-006) | **Resuelta:** a C-02 solo entra el rechazo de duración no positiva (`INVALID_DURATION`, parte mínima de US-007 CA-1 / RN-AG-09), porque un intervalo con fin <= inicio rompe la lógica de solapamiento. Granularidad de 5 min y referencias (RN-AG-11) van a C-03, medianoche (RN-AG-10) a C-04, no en el pasado (US-005) a C-07 y mensajes completos (US-006) a C-08; la zona horaria queda en C-04 (DD-09) | — | Autora |

## Riesgos del discovery (seguimiento)

| # | Riesgo | Mitigación en la KB |
|---|--------|---------------------|
| R1 | Plazo acotado: la entrega final es el jueves 2026-10-15 (el avance del 2026-10-08 solo pide el Discovery, ya hecho); trabajo individual | C-02 = solo crear turno sin solapamientos (DD-09); changes chicos y ordenados en `CHANGES.md`; plan de contingencia en 08 (recortables, en este orden: C-31, C-28, C-32, C-33, C-21; no se recortan tests) |
| R2 | Reglas de agenda incompletas (casos borde, horarios, zona horaria) | Tablas de casos borde en 06; zona y granularidad fijadas como suposiciones |
| R3 | Calidad del frontend al quedar al final | Lineamientos de UI en 08; priorización explícita |
| R4 | "Competencia sin prevención de solapamientos" es solo falta de evidencia pública | Redactado como "no evidenciado" en 01 |
| R5 | Tamaño del segmento sin datos de mercado | Sin acción en el MVP |
| R6 | Sin recordatorios por WhatsApp el MVP puede parecer incompleto | Primera evolución propuesta: enlace de WhatsApp sin API (fuera del MVP) |
| R7 | Un producto real exige Leyes 25.326 y 26.529 | Solo datos ficticios; datos mínimos; fuera de alcance del MVP |
| R8 | Evidencia de mercado basada en resúmenes de páginas | Ver limitaciones del informe |
| R9 | MVP demasiado estricto en uso real | Ver IN-03 |
| R10 | Cambio de stack impuesto por la cátedra el 2026-10-08, a una semana de la entrega: más infraestructura (PostgreSQL, Redis, Docker) y JWT, con el mismo plazo | C-02 no cambia y se prueba con pytest puro, sin Docker; Redis sin uso en el MVP (SU-11); JWT en C-19, fuera del camino de C-02; la infraestructura (C-13, C-14) corre en paralelo con el dominio y no está en el camino crítico; se mantiene el plan de contingencia de 08 |

## Puntos no evidenciados en el Discovery

Cosas que el informe (`docs/discovery/informe-discovery.md`) o el checklist dejaron como "No evidenciado", declaradas sin comprobar o sin dato. "No evidenciado" no significa que no exista: significa que no pudo constatarse con fuentes públicas. Ninguna bloquea C-02; se listan porque pueden cambiar el producto o su posicionamiento.

| # | Qué no se evidenció | Dónde en el informe | Impacto en el producto |
|---|---------------------|---------------------|------------------------|
| NE-01 | Integraciones con **ARCA/AFIP**, **Mercado Pago** y **obras sociales**: solo las declaran los proveedores (ARCA en DentalTec, ClinIA y DentalCore; Mercado Pago en DentalCore, SimpleTurno y Turnito; obras sociales en DentalTec, ClinIA, Órbita y DentalCore). Ninguna está comprobada | Resumen ejecutivo, punto 5; C.3, punto 5 | No se sabe si el mercado local ya resuelve de verdad la facturación, la seña o la liquidación. Están fuera del MVP (01); si se incorporan después, la factibilidad y el esfuerzo son desconocidos |
| NE-02 | **Ley 27.706**: sin evidencia en ningún sistema. Ley 25.326 comprobada solo en 4 sistemas; Ley 26.529 solo en Odonthia | Resumen ejecutivo, punto 4; C.3, punto 2 | No hay referencia de mercado para cumplimiento. Hoy es irrelevante (datos ficticios, sin información clínica: RN-PA-01/02), pero un producto real o con ficha clínica tendría que resolverlo desde cero (R7) |
| NE-03 | **Tamaño del segmento** (consultorios de 2 a 5 profesionales con secretaria y varios sillones): sin datos de mercado | Checklist, sección 10 (Riesgos), ítem 5 (R5); el informe no aporta cifras de segmento | La demanda real del nicho es una hipótesis. No afecta el MVP académico, pero sí cualquier decisión comercial |
| NE-04 | **Cargo extra de WhatsApp en AgendaPro** (ARS 7.900 por 50 mensajes): no verificado manualmente. Las cifras de precio de AgendaPro sí se verificaron (/ar/planes); /ar/precios no es accesible | C.3, punto 7; Verificación de fuentes (fila 5) | El costo de los recordatorios por WhatsApp como referencia de mercado es incierto. Afecta la futura evolución de recordatorios (R6) |
| NE-05 | **Nota de Open Dental (T = 5)**: no formó parte de la verificación manual del 2026-10-06; la agenda comprobada (operatorios, bloqueos, superposición solo si se habilita) se apoya en lectura de documentación vía herramienta que devuelve resúmenes | B.3 (nota sobre Open Dental); Metodología y limitaciones, puntos 1 y 8 | Open Dental es la referencia más fuerte para la regla de solapamiento por sillón; si el comportamiento real difiere, cambia el argumento de diferenciación (R4) |
| NE-06 | **Ningún sistema comprueba un rechazo estricto de solapamientos** por profesional y sillón; en 22 de los 26 figura como "No evidenciado". Odonthia avisa pero permite forzar; SimpleTurno y Agendit solo lo declaran | C.3, punto 1 | Es la base del diferenciador (R4, IN-03). Podría existir en competidores sin estar documentado: el diferenciador se redacta como "no evidenciado", no como "inexistente" |
| NE-07 | **API oficial de WhatsApp Business**: ningún sistema evidencia su uso; los recordatorios por WhatsApp solo están comprobados en Dentalink y Odonthia (en Odonthia, envío manual) | Resumen ejecutivo, punto 2; C.3, punto 7 | Sin referencia de costos ni de cumplimiento para una integración oficial; condiciona la evolución propuesta en R6 (primero enlace de WhatsApp sin API) |
| NE-08 | **Precios opacos** en el segmento local: Bilog, ClinIA, Geblix, OdontoGRAMA y OdonticLabs no publican; OdontoApp tiene una cifra no verificada; DentalTec publica solo la mensajería; varios en USD | Resumen ejecutivo, punto 5; C.3, punto 4 | No hay base sólida para fijar un precio ni para afirmar que el MVP es más barato que la competencia |
| NE-09 | **Reseñas y calificaciones** (Capterra, Google, tiendas) tomadas de fragmentos de buscadores: no verificadas y no usadas como evidencia. Las cifras de clientes son declaradas por el proveedor | Metodología y limitaciones, punto 2; A.3 | No hay dato fiable de satisfacción ni de adopción de los competidores |
| NE-10 | **Sin demos ni contacto con proveedores**: ninguna funcionalidad se probó en un producto real; solo el 2026-10-06 se verificaron manualmente 5 fuentes, el resto conserva el estado del 2026-10-03 | Metodología y limitaciones, puntos 7 y 8; D.1 | Todo el análisis de competidores se apoya en documentación pública; las diferencias de comportamiento reales (p. ej. agenda ante solapamientos) no están contrastadas |
| NE-11 | **Alojamiento de datos y normativa extranjera**: Odonthia en Brasil, DentalCore posiblemente fuera del país; los extranjeros citan RGPD o LGPD, que no equivalen a la normativa argentina | C.3, punto 2 | Una versión real tendría que decidir dónde alojar los datos y cómo cumplir la normativa local; hoy fuera de alcance (R7) |

## Campos de discovery de la KB con incertidumbre

Los seis campos de `state.kb.discovery` se infirieron con confianza razonable (`problem` desde el discovery; `stack`, `system_type` desde la decisión de stack, hoy la de la cátedra del 2026-10-08 (DD-01; ver IN-04 para el estado compartido); `scale` desde el segmento 2–5 profesionales). Única nota: [DISCOVERY] `scale` se fijó en `team` porque el consultorio es una sola organización con pocos usuarios internos; si se agregara reserva online del paciente pasaría a `public_multi_user`. Confirmar si cambia el alcance.
