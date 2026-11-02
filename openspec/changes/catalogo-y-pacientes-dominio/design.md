# Design

## Context

Ver `proposal.md` para la motivación y `docs/evidencias/explore-C-09.md` para el inventario. Copilot realizó el explore y la autora cerró D1–D13; no se presentan alternativas nuevas a esas decisiones. Las tres specs vigentes se mantienen. `Ok` de agenda tiene un campo `appointment`, `Rejected` contiene un tuple no vacío de `Violation`; la guardia permite `dataclasses`, `typing`, `collections` y módulos internos del dominio. No hay catálogo ni demo_data todavía.

## Goals / Non-Goals

**Goals:** componer altas puras, conservar contratos de agenda, datos mínimos, todas las violaciones aplicables y Strict TDD.

**Non-Goals:** edición de entidades, API, repositorios, migraciones, script de seed, matrícula, validación de teléfono/obra social, credenciales y nuevos imports permitidos. US-020 describe edición como objetivo de la aplicación completa; C-09 implementa solo el scope de altas/activación aprobado en CHANGES y D1–D13.

## Decisions

Los títulos D1–D13 identifican las decisiones cerradas de la autora. Los nombres de archivos y funciones, firmas y detalles de retorno que las concretan fueron elegidos en este propose y se enumeran aparte al final; no se atribuyen como decisiones originales del explore.

### D1 — Altas en `catalog/` y reglas en `rules/` (autora)

`catalog/create.py` compone reglas puras, como `appointment/validate.py`. Las altas reciben la entidad candidata y la colección existente cuando hace falta unicidad, y devuelven `Ok | Rejected`. El id viene del llamador, no se genera. Las reglas devuelven listas de `Violation`; no lanzan por entradas de negocio. `ValueError` queda reservado a errores de programación ya establecidos.

### D2 — Códigos y duración compartida (autora)

Agregar a `ViolationCode` solo `EMPTY_NAME`, `DUPLICATE_NAME`, `INVALID_DNI`, `DUPLICATE_DNI`. Reutilizar la lógica única de `check_duration`, incorporando el parámetro `subject: str = "del turno"`. El catálogo llama `check_duration(candidate.default_duration_min, subject="de la prestación")`: cambia solo el sustantivo del mensaje, no las razones, su orden ni `INVALID_DURATION`. Las llamadas de agenda omiten el parámetro y conservan literalmente todos los mensajes de C-03. No agregar códigos de estado repetido. No alterar `INACTIVE_REFERENCE` ni sus mensajes.

### D3 — Unicidad por `Sequence` inyectada (autora)

`create_chair(candidate: Chair, existing: Sequence[Chair])`, `create_service(candidate: Service, existing: Sequence[Service])` y `create_patient(candidate: Patient, existing: Sequence[Patient])` evalúan las colecciones recibidas, sin acceso a repositorios. `create_professional(candidate: Professional)` no necesita colección: su nombre no es único. No se modifican candidatos ni colecciones; la capa de aplicación persiste solo la entidad del resultado aceptado. La unicidad consulta todos los existentes recibidos, también inactivos; el estado no elimina una entidad del catálogo.

### D4 — Normalización de nombres para comparar (autora)

Clave equivalente a `" ".join(name.split()).casefold()`: recorta bordes y colapsa espacios internos. No se eliminan tildes ni se importa `unicodedata`. Comparar solo nombres de sillones y prestaciones. Se conserva el nombre original en las entidades, según el contrato C-08; la clave normalizada es solo para unicidad. El mensaje de duplicado usa `" ".join(candidate.name.split())`: recorta bordes y colapsa espacios internos, conservando mayúsculas y tildes; no muestra la clave con `casefold`. No cambia `subject_name`.

### D5 — Vacío no participa en duplicados (autora)

`check_name` informa una `EMPTY_NAME` si el nombre no tiene contenido. En ese caso el alta no invoca la comprobación de duplicado de nombre; sigue evaluando reglas independientes como duración. Cada duplicado produce una sola violación aunque haya varios existentes equivalentes.

### D6 — DNI normalizado y mensaje legible (autora)

Quitar puntos y espacios; exigir 7 u 8 dígitos. Guiones, letras y longitudes distintas se rechazan. Si es inválido, no evaluar duplicados de DNI, pero sí nombre. Si es válido, comparar las secuencias normalizadas de dígitos de la candidata y de los existentes. El resultado aceptado contiene una copia con `dni` compuesto solo por dígitos; no modifica la candidata. El mensaje inválido muestra el valor recibido entre comillas; el duplicado usa puntos de miles para 7 u 8 dígitos.

### D7 — Activación por copia, idempotente (autora)

`catalog/activation.py` expone `deactivate` y `reactivate` para Professional, Chair y Service, usando `dataclasses.replace` y conservando el tipo concreto. Devuelven directamente la entidad copiada con el estado pedido; no necesitan `Rejected`, porque no hay una regla de negocio que falle. En un estado ya igual, los valores del resultado son iguales y no hay violación; no se exige identidad de objeto. Patient no tiene active. Las funciones no reciben turnos y no pueden alterarlos. Los tests ejercitan el rechazo de nuevos turnos a través de `validate_new_appointment`, sin duplicar reglas.

### D8 — Modelo mínimo y migración mecánica (autora)

- `Service(id, name, default_duration_min, active=True)`.
- `Patient(id, full_name, dni, phone: str | None = None, health_insurance: str | None = None)`.
- `Professional(id, full_name, active)` y `Chair(id, name, active)` siguen iguales.
- Dataclasses frozen/slots, sin validación de negocio al construir. Patient tiene exactamente los cinco campos anteriores, sin clínica ni active.
- `license_number` se reserva a C-15; teléfono/obra social conservan texto libre, incluido vacío. Migrar constructores existentes con datos ficticios sin cambiar sus expectativas de agenda.

### D9 — Todas las violaciones, ordenadas (autora)

Componer sin retorno anticipado: `EMPTY_NAME` → `INVALID_DNI` → `DUPLICATE_NAME` o `DUPLICATE_DNI` → `INVALID_DURATION`. No todas aplican a cada entidad: profesional solo nombre; sillón nombre/duplicado; prestación nombre/duplicado/duración; paciente nombre/DNI/duplicado. Las guardas D5 y D6 solo descartan el duplicado dependiente, no las otras comprobaciones. Las violaciones nuevas no llevan `reference_kind`, ids ni intervalo en conflicto, que siguen reservados a los contratos de agenda.

### D10 — Demo data fuera del dominio (autora)

`backend/app/demo_data.py` expone colecciones inmutables de entidades ficticias, con UUID literales y deterministas. Incluye profesional «Dra. Laura Quiroga», sillón «Sillón 1», prestación «Limpieza» (45 min), paciente «Ana Pérez» con DNI `30111222`; todos son ejemplos ficticios. Puede importar el dominio; la dependencia inversa está prohibida. Sin acceso a BD, reloj, generación de UUID, secretos ni script ejecutable de seed. Tests de reglas usan datos literales de la spec; un test separado demuestra reutilización de demo_data mediante altas públicas.

### D11 — Capacidad nueva (autora)

Solo `specs/catalog-and-patients/spec.md`, con Purpose y ADDED Requirements. No modificar las specs principales ni crear un delta de agenda. La regresión sobre agenda conserva todos sus requisitos, incluido `Ok.appointment` y la no validación al construir nombres.

### D12 — Textos exactos (autora)

Los nuevos mensajes están en la spec; cada texto se prueba completo. Nombre de duplicado recortado y con espacios internos colapsados, conservando mayúsculas y tildes: `"  SILLÓN   1  "` se muestra como `"SILLÓN 1"`. DNI inválido muestra el original; duplicado muestra puntos de miles. Duración de catálogo dice «La duración de la prestación» y conserva literalmente las razones de `rules/duration.py` para 0, -5, 7, 485 y 487 minutos; la agenda conserva «La duración del turno» mediante el valor predeterminado de D2. Un test de regresión compara los cinco mensajes completos de C-03 sin cambiar ninguna expectativa existente.

### D13 — BAJO, sin punto de control (autora)

Tasks describe ciclos verticales RED/GREEN/TRIANGULATE/REFACTOR y mutaciones restauradas. No hay tarea de aprobación intermedia. En este propose no se escribe código ni tests.

### Detalles técnicos definidos en este propose (no nuevas reglas de negocio)

1. **Resultado de catálogo separado:** `catalog/result.py` define su propio `Ok[T]` frozen/slots con `entity: T` y alias `CatalogResult[T] = Ok[T] | Rejected`; reutiliza `Rejected` y `Violation` vigentes. Este tipo es distinto de `app.domain.violations.Ok`: no lo reemplaza, generaliza ni modifica, y tampoco cambia `ValidationResult`. Ningún código ni test existente que use `Ok.appointment`, sus imports o sus expectativas cambia por esta decisión. Las migraciones mecánicas de constructores de Service/Patient de D8 no afectan el contrato `.appointment`. En imports nuevos ambiguos se usan alias explícitos `CatalogOk` y `AppointmentOk`.
2. **Seams públicos planificados:** altas en `catalog/create.py` (aceptación/rechazo de usuario), activación en `catalog/activation.py` (copia/estado), `validate_new_appointment` (regresión real), constructores/`dataclasses.fields` (contrato del modelo), demo_data y guardias estáticas existentes (datos y dirección de dependencias). Las altas detectan errores y orden; no prueban persistencia ni API. Esos seams concretan los límites públicos pedidos; se documentan para su revisión con el propose, sin abrir un checkpoint.
3. **Reglas pequeñas:** `rules/catalog_names.py` y `rules/dni.py` evitan mezclar unicidad con el helper gramatical `subject_name`. Se prueban los efectos de composición por las altas; no se inspeccionan funciones privadas ni se mockean colaboradores.
4. **Tipos/ejemplos:** TypeVar restringido a tipos de entidad para conservar inferencia en Python 3.12/mypy; UUID literales y datos del spec. No se añaden dependencias ni herramientas: verificación con pytest y mypy existentes, estilo revisado a mano como C-08.
5. **Forma de activación:** devolver directamente la copia tipada, sin wrapper, concreta D7; D1 pide `Ok | Rejected` para las altas, no para operaciones de estado que no fallan. Idempotencia se verifica por valores, sin imponer identidad. Conservar el nombre original aplica la garantía vigente de C-08; normalizarlo para comparar no cambia su almacenamiento.

## Risks / Trade-offs

- [Constructores nuevos obligatorios] → migración mecánica con baseline previo y chequeo mypy; si un test existente falla sin explicación se detiene.
- [Dos `Ok` con distinto payload] → namespaces separados y alias explícitos; no cambia contrato de agenda.
- [Unicidad solo sobre lo recibido] → el llamador debe suministrar la colección completa; concurrencia/persistencia quedan para C-15 y capas posteriores, sin pretender garantía transaccional aquí.
- [Parámetro compartido de duración] → valor predeterminado «del turno», catálogo explícitamente «de la prestación» y regresión de los cinco mensajes completos de C-03; las razones siguen teniendo una sola implementación.
- [Guardias estáticas no detectan imports/reloj dinámicos] → conservar limitación documentada de C-01/C-07; no usar imports dinámicos ni alias de reloj para eludirlas.

## Migration Plan

Durante apply: baseline de suite y tipos; nuevos tests del modelo en rojo, cambios mínimos de campos y adaptación mecánica de constructores; luego ciclos de comportamiento uno por uno. No se migra BD ni hay despliegue. No se hace commit ni rollback Git sin pedido expreso.

## Open Questions

Ninguna que afecte el alcance o las decisiones D1–D13. Los detalles técnicos anteriores se hacen explícitos para que el apply no tenga que rediseñar contratos.
