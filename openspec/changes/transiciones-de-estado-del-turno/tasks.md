# Tasks

Gobernanza MEDIO; decisiones D1–D10 cerradas, sin checkpoint ni aprobación intermedia. Este archivo planifica el apply: nada se ejecuta durante propose. Antes de modificar existentes correr Safety Net; fallos previos obligan detener y reportar sin arreglos fuera de alcance. Cada tarea de producción exige RED escrito y ejecutado con fallo esperado antes de GREEN mínimo; agregar casos de triangulación uno por ciclo (mínimo dos por comportamiento) y ejecutar después de cada refactor. No escribir todos los tests primero. Regresiones que ya pasan se registran como tales; una mutación restaurada demuestra sensibilidad, pero no sustituye el RED obligatorio de comportamiento nuevo.

Seams definidas por contratos cerrados: Actor/Role, cancel_appointment, change_status y validate_new_appointment. Consulta técnica pública can_transition: prueba solo política, sin actor/now. La prueba de 25 pares usa oráculo independiente, no tabla productiva. Tests de operaciones fijan actor autorizado y now igual al inicio al aislar transición; tiempos y permisos tienen pruebas separadas. Guardias ejercitan pureza real, no persistencia. Datos literales del spec, UUID distintos para user/professional y now UTC; sin mocks/patch/monkeypatch/freezegun/Any. Cargar tdd, python-testing-patterns y python-pro en apply con overlay de reglas duras.

## 1. Safety Net

- [x] 1.1 Inspeccionar diff/estado y ejecutar desde backend la suite pytest existente y mypy estricto con el intérprete del venv disponible; registrar comandos, número real y resultados. Detener ante fallo preexistente. No asumir conteos del archivo de C-09 ni instalar dependencias.
- [x] 1.2 Identificar expectativas/imports vigentes de Ok.appointment, catálogo y guardia. Conservar trabajo ajeno y limitar cambios a Impact. Preparar evidencia por tarea con columnas Test File, Layer, Safety Net, RED, GREEN, TRIANGULATE, REFACTOR; no marcar tareas sin evidencia real.

## 2. Actor

- [x] 2.1 RED en test_model.py: construir Actor con UUID de usuario distinto al profesional y Role.ODONTOLOGO; GREEN mínimo Actor/Role en model.py frozen/slots. TRIANGULATE recepción y administrador sin professional_id; comprobar campos, default None e inmutabilidad de role/professional_id.
- [x] 2.2 RED odontólogo sin professional_id; GREEN ValueError de programación en constructor. TRIANGULATE omisión y None explícito, conservando roles de gestión válidos. REFACTOR docstrings/tipos y ejecutar tests de modelo y mypy tras cada cambio.

## 3. Política única

- [x] 3.1 RED consulta pública can_transition para reservado a confirmado; GREEN mínimo en appointment/transitions.py. TRIANGULATE las otras aristas y un rechazo confirmado a reservado, uno por ciclo, generalizando hacia un dict privado del módulo declarado como Mapping[AppointmentStatus, frozenset[AppointmentStatus]], importando Mapping de collections.abc o typing ya permitidos; cinco claves, siete aristas exactas y sin referencia mutable externa.
- [x] 3.2 Completar parametrize con producto de los cinco estados, 25 pares, expectativas independientes descritas en design; ejecutar antes de corregir cualquier arista pendiente. Verificar cinco diagonales y tres terminales. No obtener expected de tabla/can_transition ni copiar matriz 5x5. Mutar una arista permitida y una prohibida por separado, demostrar fallo y restaurar; registrar resultados reales.
- [x] 3.3 Verificar con mypy que el contrato Mapping no permite asignar destinos y que los destinos frozenset no permiten mutación; la garantía del mapa es estática, no un rechazo de asignación en ejecución. Mantener el dict privado del módulo. REFACTOR de consulta y tipos, ejecutar tests y guardias vigentes sin modificar la allowlist.

## 4. Cancelación

- [x] 4.1 RED cancel_appointment reservado con recepción y now 09:00 local; GREEN devolver Ok de agenda con copia cancelada y campos intactos. Añadir tres códigos aprobados a ViolationCode solo a medida que los fallos los requieran; no usar Ok de catálogo. TRIANGULATE confirmado con administración y original sin cambios.
- [x] 4.2 RED cancelar atendido; GREEN INVALID_TRANSITION con texto exacto. TRIANGULATE ausente y cancelado terminal, casos independientes, comprobando todos los campos del original y metadatos None; cinco diagonales se completan por ambas operaciones, sin idempotencia.
- [x] 4.3 TRIANGULATE cancelación después del inicio y después del fin con estados no terminales; registrar como regresión verde si no requiere lógica nueva. No añadir regla de pasado ni anticipación mínima. REFACTOR composición de cancelar, actualizar docstring de Ok a turno aceptado por alta/transición manteniendo payload/imports; ejecutar regresiones de agenda/catálogo y mypy.

## 5. Cambio de estado y contrato

- [x] 5.1 RED change_status reservado a confirmado; GREEN mínimo con copia y ValidationResult. TRIANGULATE reservado/confirmado a atendido y ausente con now igual a inicio, una arista por ciclo. Conectar las siete aristas por la consulta única: cancelaciones se ejecutan por cancel_appointment, nunca por change_status(CANCELLED).
- [x] 5.2 RED target CANCELLED en change_status; GREEN ValueError que indica usar cancel_appointment. TRIANGULATE con odontólogo ajeno para demostrar que guarda de programación precede permiso. RED target RESERVED desde confirmado si no rechaza aún; GREEN INVALID_TRANSITION; TRIANGULATE reservado a reservado. No convertirlo en reprogramación.
- [x] 5.3 RED now naive en cancel_appointment; GREEN validación/normalización UTC. TRIANGULATE now naive en change_status y equivalencia de now 10:00-03:00/14:00+01:00 (ambos13:00 UTC), preservando comparación exacta. Errores de programación ValueError; negocio nunca excepción. REFACTOR guardas y exportaciones en appointment/__init__.py, ejecutar tests/mypy.

## 6. Permisos

- [x] 6.1 RED odontólogo ajeno que cambia estado; GREEN FORBIDDEN_OPERATION con mensaje exacto. TRIANGULATE propios confirmado/atendido/ausente con U1 distinto de P1 y ajenos con dos destinos; comparar professional_id, no user_id, sin JWT ni consultas externas.
- [x] 6.2 RED odontólogo que cancela propio; GREEN prohibición específica de cancelación y texto exacto. TRIANGULATE cancelación ajena y ambos roles de gestión sobre T1/T2 en ambas operaciones. Comprobar que change_status(CANCELLED) conserva ValueError contractual y no permite bypass.
- [x] 6.3 REFACTOR política por operación/rol/propiedad manteniendo decisiones, sin jerarquía extra de roles; ejecutar tests de permisos, guardias y mypy. No tocar autenticación de C-19 ni matriz de KB.

## 7. Tiempo y composición

- [x] 7.1 RED atendido antes del inicio con now 09:00 local; GREEN STATUS_CHANGE_TOO_EARLY exacto. TRIANGULATE ausente temprano, igualdad exacta, un microsegundo antes/después, segundos09:59:30, durante el turno antes del fin y confirmación antes/después; ejecutar cada caso y generalizar solo ante fallo. No usar check_not_in_the_past ni comparar con fin.
- [x] 7.2 RED actor autorizado en terminal que solicita atendido antes del inicio: debe recibir INVALID_TRANSITION seguido de STATUS_CHANGE_TOO_EARLY. GREEN acumulación de ambos. TRIANGULATE destino ausente y caso con tiempo cumplido (solo transición).
- [x] 7.3 RED actor no autorizado con transición y tiempo inválidos: solo FORBIDDEN_OPERATION. GREEN corte por permiso. TRIANGULATE otro destino y cancelación propia terminal por odontólogo (solo permiso). REFACTOR orden guardas/permiso/transición/tiempo; ejecutar después de cada cambio y mypy.

## 8. Mensajes y metadatos

- [x] 8.1 Comparar completos los cinco textos normativos: transición, atendido temprano, ausente temprano, ajeno y cancelación prohibida. Para cada texto nuevo pendiente, RED antes de GREEN, sin cambiar expectativas. TRIANGULATE nombre recortado, vacío, blanco e internos dobles; fallback exacto `el profesional`; no añadir artículos ni colapsar interiores.
- [x] 8.2 TRIANGULATE fecha local distinta del día UTC, now con segundos siempre y formatos locales de inicio/fin. Reutilizar format_local_* existentes sin alterar contratos previos; datos locales y UTC literales. RED de metadatos si hay información incorrecta; GREEN mantener los cuatro campos None en todos los códigos. REFACTOR helper de mensaje sin modificar nombres en entidades ni usar id propio como conflicto.

## 9. Integración y regresión

- [x] 9.1 RED composición cancelar reservado y validar nueva reserva mismo profesional/sillón/intervalo usando copia devuelta, con contexto válido y now 09:00 local; GREEN solo cableado faltante. TRIANGULATE origen confirmado y control previo que produce ambos solapamientos con versión original. Si la composición ya pasa, registrar regresión verde sin falsear RED ni cambiar reglas vigentes.
- [x] 9.2 Verificar ATTENDED sigue ocupando y NO_SHOW no ocupa, catálogo conserva Ok.entity y altas Ok.appointment reservado, sin actor obligatorio nuevo ni historial. Mantener OCCUPYING_STATUSES y reglas existentes sin diff. Mutación controlada de cableado puede comprobar sensibilidad, siempre restaurada, sin adoptar cambios a las reglas.

## 10. Verificación final del apply

- [x] 10.1 Ejecutar suite completa pytest y mypy estricto; guardias reales de imports/reloj limpias, sin modificar su allowlist. Revisar no Any, I/O, generación de UUID, reloj global, historial, reprogramación ni dependencias nuevas. Revisar estilo/docstrings sin instalar herramientas.
- [x] 10.2 Trazar cada escenario del delta appointment-lifecycle y cada variante de matriz/roles/tiempo a tests concretos PASSED; completar tabla TDD y registrar baseline, RED/GREEN, triangulación, refactor y mutaciones restauradas, sin evidencias inventadas. Reportar cualquier desvío real.
- [x] 10.3 Revisar diff y diff --check: cambios limitados a Impact, sin KB/main specs/CHANGES/AGENTS/CLAUDE/state, sin stage/commit/push/archive. Reportar resultados y tareas; no ejecutar CLI OpenSpec mientras siga vigente la instrucción de la autora.
