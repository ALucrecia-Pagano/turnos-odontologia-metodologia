# Explore de C-09 catalogo-y-pacientes-dominio

El explore lo hizo Copilot. La autora cerró las decisiones D1 a D13 y pidió documentarlas con Codex el 2026-11-01, antes del propose. Este documento registra esas decisiones; no implementa código ni reabre opciones.

## Punto de partida

- C-02 a C-08 están archivados; no había changes activos. C-09 depende de C-02, ya cumplido.
- `backend/app/domain/model.py`: `Professional(id, full_name, active)` y `Chair(id, name, active)` ya conservan el nombre original sin validar; `Service(id, default_duration_min, active=True)` todavía no tiene nombre y `Patient(id)` solo tiene identificador. Son dataclasses inmutables con slots.
- `appointment/validate.py` compone reglas puras y devuelve `violations.Ok(appointment)` o `Rejected(violations)`. El alta del catálogo todavía no existe. El `Ok` vigente es específico de turnos y su contrato debe conservarse.
- `rules/duration.py::check_duration` ya implementa RN-AG-09, con una sola `INVALID_DURATION` y mensajes completos. Se reutiliza sin cambiar mensajes, incluso su expresión «duración del turno».
- `rules/names.py::subject_name` solo recorta el nombre para mostrarlo en conflictos; no normaliza unicidad. La normalización del catálogo tiene otra finalidad.
- `rules/references.py` ya rechaza profesional, sillón y prestación inactivos con `INACTIVE_REFERENCE`; no cambia en C-09.
- Las reglas de horario, bloqueos, grilla, medianoche, pasado y solapamientos no necesitan cambios. El dominio recibe UUID y tiempo; no los genera ni hace I/O.
- Specs vigentes: `appointment-scheduling` (26 requisitos / 167 escenarios), `backend-toolchain` (6 / 9) y `domain-dependency-guard` (7 / 34). La guardia permite stdlib acotada y módulos internos del dominio; no permite `unicodedata` ni `app.demo_data`.
- KB 04 ya describe nombres, DNI único, teléfono y obra social como texto, sin clínica. `license_number` pertenece al modelo persistido; se aclara su exclusión del dominio C-09.
- US-020 menciona edición como objetivo general, pero el scope C-09 y las decisiones aprobadas cubren altas y activación; edición, persistencia y seed ejecutable quedan fuera.

## Decisiones

| # | Decisión cerrada por la autora |
|---|---|
| D1 | Altas en `backend/app/domain/catalog/`, componiendo reglas puras de `rules/`, con `Ok | Rejected` y `Violation`; `ValueError` solo para errores de programación. |
| D2 | Nuevos códigos `EMPTY_NAME`, `DUPLICATE_NAME`, `INVALID_DNI`, `DUPLICATE_DNI`. Duración reutiliza `check_duration`, `INVALID_DURATION` y sus mensajes actuales. Sin `ALREADY_INACTIVE` ni `ALREADY_ACTIVE`; no cambia `INACTIVE_REFERENCE`. |
| D3 | Unicidad contra una `Sequence` de entidades existentes recibida por parámetro, sin BD. |
| D4 | Igualdad de nombres: recortar bordes, colapsar espacios internos a uno, `casefold`. Tildes significativas; sin `unicodedata`. Solo `Chair.name` y `Service.name` son únicos; nombres de profesional y paciente pueden repetirse. |
| D5 | Nombre vacío o en blanco produce `EMPTY_NAME`; no se evalúa duplicado para ese nombre. |
| D6 | DNI: quitar puntos y espacios; deben quedar 7 u 8 dígitos. Guiones no aceptados. Se guardan solo dígitos y se comparan por ellos. Un DNI inválido no participa en duplicados. El mensaje de duplicado usa puntos de miles. |
| D7 | Desactivar/reactivar devuelven copia con `active=False`/`True` mediante `dataclasses.replace`; idempotentes y sin violación. No cambian turnos existentes. Un turno nuevo con referencia inactiva conserva el rechazo existente. |
| D8 | `Service(id, name, default_duration_min, active=True)`; `Patient(id, full_name, dni, phone=None, health_insurance=None)`, exactamente esos cinco campos y sin clínica. Migración mecánica de constructores de tests. Sin `license_number` hasta C-15. Teléfono y obra social libres. |
| D9 | Todas las violaciones del alta juntas: `EMPTY_NAME`, `INVALID_DNI`, `DUPLICATE_NAME` o `DUPLICATE_DNI`, `INVALID_DURATION` al final. Las guardas D5/D6 no impiden evaluar las otras reglas. |
| D10 | Datos ficticios reutilizables en `backend/app/demo_data.py`, fuera del dominio; el dominio no lo importa. Sin script de seed ni contraseñas. |
| D11 | Capacidad nueva `catalog-and-patients`, solo requisitos ADDED, separada de `appointment-scheduling`. |
| D12 | Mensajes exactos en la tabla siguiente; duplicado de nombre usa el nombre ingresado recortado, conservando mayúsculas y espacios internos. |
| D13 | Governance BAJO; no hay punto de control en tasks. |

### Mensajes exactos

| Código | Texto |
|---|---|
| EMPTY_NAME | `El nombre del profesional no puede estar vacío.` / `El nombre del sillón no puede estar vacío.` / `El nombre de la prestación no puede estar vacío.` / `El nombre del paciente no puede estar vacío.` |
| DUPLICATE_NAME | `Ya existe un sillón con el nombre "Sillón 1".` / `Ya existe una prestación con el nombre "Limpieza".` |
| INVALID_DNI | `El DNI no es válido (se recibió "30-111-222"): debe tener 7 u 8 dígitos, con o sin puntos.` |
| DUPLICATE_DNI | `Ya existe un paciente con el DNI 30.111.222.` |

## Pedidos para el propose

Nueva spec ADDED con altas de las cuatro entidades, validación y unicidad normalizadas, DNI, duración reutilizada, acumulación ordenada, activación idempotente, protección de turnos existentes, modelo mínimo y datos ficticios. Planificar Strict TDD por comportamiento con RED ejecutado, GREEN mínimo, triangulación, mutaciones restauradas y evidencias finales comparables con C-08. No se escribe código ni tests en este propose.
