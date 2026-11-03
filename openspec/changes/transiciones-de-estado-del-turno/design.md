# Design

## Context

El modelo ofrece cinco estados y Appointment frozen/slots con tiempos UTC. `violations.Ok.appointment` acepta un Appointment; su docstring todavía habla de turno nuevo reservado. El Ok de catálogo es distinto y no se reutiliza. `rules/overlap.py` ya excluye cancelado/ausente y comparte OCCUPYING_STATUSES con bloqueos. No existen actor ni operaciones de transición. La autora cerró D1–D10 y confirmó SU-03/SU-08 para este change; se documenta aquí y se registra la confirmación en la KB.

CHANGES C-10 y el disparador de KB07 Flujo 3 pueden sugerir que un odontólogo cancela sus turnos. La decisión cerrada aplica la matriz específica KB03 RBAC: odontólogo nunca cancela; sí cambia confirmado/atendido/ausente propios. No se reabre esa contradicción. El historial descrito por Flujo 3 corresponde a C-12, no a esta implementación.

## Goals / Non-Goals

Goals: tabla única, contratos tipados, pureza, copias, permisos por operación y propiedad, tiempo preciso y mensajes locales; Strict TDD exhaustivo.

Non-Goals: reprogramar o volver a reservado por reprogramación (C-11), historial (C-12), JWT/credenciales, consultas a usuarios, API, BD, dependencias externas nuevas, cambios de reglas de agenda/catálogo o de OCCUPYING_STATUSES.

## Decisions

### D1 — Tabla única inmutable

La tabla vive en `appointment/transitions.py`, con cinco orígenes y destinos frozenset: RESERVED a CONFIRMED/ATTENDED/NO_SHOW/CANCELLED; CONFIRMED a ATTENDED/NO_SHOW/CANCELLED; los tres terminales a conjunto vacío. Siete aristas, sin diagonales. Declarar la tabla como `Mapping[AppointmentStatus, frozenset[AppointmentStatus]]`, con `Mapping` importado de `collections.abc` o `typing`, ya permitidos. Usar un dict privado del módulo, sin exponer una referencia mutable externa. La inmutabilidad del mapa la garantiza el tipo para mypy; los destinos son frozensets. La guardia de dependencias y su allowlist no se modifican en C-10. Una consulta pública pura `can_transition(origin, target)` permite verificar los 25 pares sin invocar una operación fuera de su contrato.

### D2 — Operaciones y resultado vigente

`cancel_appointment(appointment: Appointment, actor: Actor, now: datetime, professional_name: str, tz: ZoneInfo) -> ValidationResult`.

`change_status(appointment: Appointment, target: AppointmentStatus, actor: Actor, now: datetime, professional_name: str, tz: ZoneInfo) -> ValidationResult`.

Ambas reciben todos los datos, sin I/O ni reloj global. Verificar now aware y normalizar UTC, aun en cancelación; naive es ValueError de programación. change_status con CANCELLED lanza ValueError que indica usar cancel_appointment: evita saltar la política específica de cancelación. RESERVED devuelve INVALID_TRANSITION, no reprograma. Los errores de contrato se verifican antes de las reglas de negocio.

Reutilizar exclusivamente `app.domain.violations.Ok`, Rejected y ValidationResult. Un éxito devuelve copia mediante dataclasses.replace con solo status cambiado; conservar id, paciente, profesional, sillón, prestación e intervalo. No mutar original. Ajustar solo la documentación de Ok para admitir turno aceptado por alta o transición; mantener `.appointment`, imports y consumidores vigentes. Sin entrada de historial ni ids nuevos.

### D3 — Actor y permisos

Actor frozen/slots: `user_id: UUID`, `role: Role`, `professional_id: UUID | None = None`. Role tiene ODONTOLOGO, RECEPCION, ADMINISTRADOR, con valores de rol en español consistentes con la KB. ODONTOLOGO sin professional_id es ValueError al construir: contexto incoherente del llamador, no regla de negocio. No exigir vínculo a recepción/administración ni usar user_id como professional_id.

Odontólogo: change_status solo si actor.professional_id coincide con appointment.professional_id; cancel_appointment siempre prohibido, incluso propio. Recepción y administrador: ambas operaciones sobre todos. El actor llega autenticado por el borde futuro; dominio no recibe ni verifica JWT. user_id se conserva como identidad para la integración posterior, sin historial en C-10.

### D4 — Códigos y mensajes exactos

Agregar únicamente INVALID_TRANSITION, STATUS_CHANGE_TOO_EARLY, FORBIDDEN_OPERATION. Los textos exactos y variantes son normativos en la spec. El prefijo identifica `El turno de {nombre} del {fecha local} de {inicio local} a {fin local} (hora local)`; aplicar strip al nombre, sin colapsar espacios internos ni modificar la entidad; vacío/blanco usa `el profesional`. Reutilizar format_local_date_time, format_local_time y format_local_date_time_with_seconds; fecha del día local y now siempre con segundos. La zona se inyecta.

No usar conflicting_appointment_id para el turno operado: no es otro turno en conflicto. reference_kind, ambos ids de conflicto y conflicting_interval permanecen None en las tres violaciones. Los errores de negocio nunca se lanzan.

### D5 — Tiempo

Para destinos ATTENDED/NO_SHOW rechazar solo now < appointment.start_at, comparando instantes con segundos/microsegundos, sin truncar ni tolerancia. Igualdad es válida; el fin no interviene. Confirmación no impone tiempo; cancelar no tiene anticipación mínima y es posible después del inicio/fin si el estado sigue reservado/confirmado y el actor tiene permiso. No reutilizar check_not_in_the_past: valida otra operación y tiene mensaje de sentido diferente.

### D6 — Orden y guardas

Tras las guardas de contrato, permiso primero: si falla, Rejected solo con FORBIDDEN_OPERATION. Si pasa, evaluar todas las aplicables: INVALID_TRANSITION y luego STATUS_CHANGE_TOO_EARLY. El tiempo se evalúa para ATTENDED/NO_SHOW incluso si la arista es inválida. Una operación autorizada puede devolver ambas; no aplicar RN-AG-12 de altas como si definiera esta prioridad.

### D7 — Liberación mediante ocupación existente

No cambiar OCCUPYING_STATUSES: RESERVED, CONFIRMED, ATTENDED. La copia cancelada no pertenece al conjunto y deja de causar ambos solapamientos. El llamador debe reemplazar la versión anterior por la devuelta. No borrar turno, quitar recursos ni crear flags; otras restricciones de agenda siguen vigentes. NO_SHOW también libera como ya prescribe la spec vigente; ATTENDED sigue ocupando.

### D8 — Mismo estado

Los cinco pares diagonales producen INVALID_TRANSITION. cancelado a cancelado se prueba por cancel_appointment; confirmado a confirmado por change_status. No inferir idempotencia a partir del catálogo. change_status(CANCELLED) conserva su ValueError contractual incluso si origen cancelado; la consulta can_transition y cancel_appointment cubren la diagonal de cancelación.

### D9 — Pruebas exhaustivas sin oráculo circular

Parametrize genera producto cartesiano de los cinco valores de AppointmentStatus: 25 pares por can_transition, consulta que no recibe actor ni now. expected proviene de propiedades independientes de RN-TU-02, expresadas en el test sin importar ni reconstruir con la tabla productiva: reservado admite los otros cuatro; confirmado solo atendido/ausente/cancelado; terminales no salen; diagonales inválidas. No copiar una matriz 5x5 ni calcular expected llamando can_transition. Casos literales complementan cada arista por las operaciones: actor autorizado y now igual al inicio para aislar la transición, cancelado por cancel_appointment y los demás destinos por change_status dentro de su contrato.

Seams definidas por los contratos cerrados: constructores Actor/Role y errores de contrato; cancel_appointment y change_status (composición observable de actor/tiempo/resultado); validate_new_appointment y guardias existentes (integración real y pureza, sin persistencia). can_transition es la consulta pública técnica para los 25 pares, sin verificar autenticación. Probar cada borde temporal, roles y propiedad, mensajes completos, metadatos y originales intactos. Datos literales, UTC inyectado, sin mocks/patch/monkeypatch/freezegun ni Any. Una cancelación desde reservado y otra desde confirmado triangulan liberación; cada comportamiento debe tener al menos dos casos.

### D10 — Sin punto de control ni historial

Decisiones cerradas; tasks no incluye aprobación intermedia. Mantener el ciclo Safety Net → RED ejecutado → GREEN mínimo → TRIANGULATE → REFACTOR con ejecución tras cada cambio. Si una regresión ya pasa por composición, registrarla honestamente como verde y demostrar sensibilidad con una mutación restaurada, sin inventar un RED; esto no sustituye el RED obligatorio para producción nueva. No agregar modelos ni payload de historial.

## Risks / Trade-offs

- API pública y consulta de tabla tienen alcances distintos: CANCELLED es válido como destino de tabla, pero usarlo en change_status es error contractual. Tests separados evitan borrar una arista para satisfacer la operación.
- Odontólogo se identifica por professional_id, no user_id; usar UUID diferentes en los escenarios detecta la confusión.
- Permiso corta: no se mezclan fallos posteriores para actor no autorizado. Actor autorizado sí recibe transición y tiempo, aun sobre terminal.
- Cancelar libera solo si el llamador utiliza la copia devuelta; probar el flujo completo, manteniendo demás reglas válidas.
- Los formatos existentes omiten microsegundos en mensajes aunque comparación los conserva; no alterar formateadores ni reglas anteriores.
- Reprogramar confirmado a reservado es una operación C-11 distinta; no ampliar tabla ordinaria ni scope.

## Migration Plan

Apply futuro: baseline real de suite/mypy, luego ciclos verticales por comportamiento y regresión completa. No hay migración de datos ni despliegue. Reutilizar contratos e imports existentes, con exportaciones nuevas en appointment. No ejecutar validaciones ni implementar durante este propose. Artefactos creados manualmente por override explícito del usuario, con metadata spec-driven local; sin atribuir estado o validación al CLI.

## Open Questions

Ninguna que afecte D1–D10: cerradas por la autora. SU-03/SU-08 confirmadas por la autora el 2026-11-02 y registradas en la KB, conservando el texto original.

## Desvíos del apply

1. Varios casos de triangulación y regresión pasaron inicialmente por composición. Se conservaron como verdes iniciales y se aplicaron mutaciones restauradas: Actor/default/frozen, política/aristas, copias, terminales, cancelación tardía, propiedad, permisos, igualdad/fin, orden/corte, nombres/segundos/metadatos, diagonales, integración y tipos. No se atribuye RED original a esos casos. El registro textual incluye salidas y restauraciones.
2. La triangulación de gestión/frozen de 2.1 se añadió como pequeño grupo antes de ejecutar los cinco casos; las restantes aristas/casos se incorporaron por ciclos. 5.1 se marcó antes de conectar change_status con can_transition; la conexión se completó en el RED/GREEN de 5.2. Las tres diagonales restantes por operación y la automatización de los dos rechazos estáticos se completaron en la revisión final, con pruebas y mutaciones restauradas.
3. Se inició el RED/GREEN de 7.1 antes de leer la salida asíncrona de mypy de 6.3. Esta contenía comparison-overlap en ramas constantes de tests nuevos. Se detuvo el avance de 7, se simplificaron exclusivamente esas ramas conservando todos los tests/aserciones, y 6.3 volvió a verde (38 pruebas con guardias, mypy48) antes de continuar. No se usaron ignores ni se modificaron expectativas previas.
4. El sandbox negó inicialmente acceso al Python313 externo del venv. Los mismos comandos funcionaron con ejecución escalada, sin instalar ni cambiar entorno. Un helper PowerShell no se ejecutó por política de scripts; se eliminó y se capturaron comandos directos. Un primer import del helper Python usó nombre incorrecto, corregido antes de ejecutar pruebas.
5. La primera prueba negativa mypy con -c heredó files de pyproject y devolvió error de invocación; se repitió con configuración aislada y produjo los dos errores de tipos esperados. La automatización final usa un archivo temporal mypy.ini con strict=True. Una selección pytest con expresión compuesta se separó incorrectamente en el helper: exit4 no se cuenta como mutación válida; corregido el parseo, se repitió y produjo dos fallos de aserción y dos verdes tras restaurar.
6. Automatic approval review rechazó un script de refactor que reemplazaba el tramo final de los tests por riesgo de borrar pruebas. No se ejecutó. La alternativa segura simplificó patrones exactos de ramas constantes y comprobó preservar la lista de funciones de test; todas las aserciones quedaron intactas. No queda acción bloqueada ni se necesita aprobación.
7. El nuevo test de compatibilidad llamó inicialmente create_professional con dos parámetros, provocando TypeError; se corrigió la llamada al contrato existente con el candidato Professional. No se cambió ningún esperado ni código de catálogo, y el test pasó.
8. Black/ruff no están instalados; se revisó estilo/docstrings manualmente y se ejecutaron tests/mypy después del refactor. Se conservan los 483 tests anteriores sin cambiar valores esperados ni textos. No se ejecutó OpenSpec por instrucción expresa; no se afirma validación CLI.
