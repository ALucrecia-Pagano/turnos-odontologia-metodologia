# Proposal

## Why

La agenda ya valida turnos, pero las entidades mínimas todavía no ofrecen altas de catálogo ni pacientes con DNI único. C-09 incorpora esas reglas puras y datos ficticios reutilizables para preparar persistencia y API sin llevar I/O al dominio.

## What Changes

- Altas de profesionales, sillones, prestaciones y pacientes con resultados tipados, nombres obligatorios, unicidad normalizada donde corresponde y DNI normalizado.
- Nuevos códigos `EMPTY_NAME`, `DUPLICATE_NAME`, `INVALID_DNI`, `DUPLICATE_DNI`; duración reutiliza `check_duration` con sujeto parametrizado: «de la prestación» para catálogo y «del turno» por defecto, preservando los textos de C-03. Los mensajes de nombre duplicado recortan bordes y colapsan espacios internos, conservando mayúsculas y tildes.
- Desactivar y reactivar profesionales, sillones y prestaciones de forma inmutable e idempotente, sin cambiar turnos existentes.
- **BREAKING**: `Service` agrega `name` obligatorio y `Patient` agrega `full_name` y `dni` obligatorios más dos opcionales; los llamadores actuales se migran mecánicamente. No cambia el comportamiento de agenda ni `Ok.appointment`.
- Datos ficticios en `app/demo_data.py`, fuera del dominio; sin seed ejecutable, persistencia, API ni nuevas dependencias.

## Capabilities

### New Capabilities

- `catalog-and-patients`: altas validadas del catálogo y de pacientes, activación de recursos y datos mínimos ficticios, con reglas puras y errores explicativos.

### Modified Capabilities

Ninguna. La compatibilidad de agenda se comprueba mediante regresión y escenarios nuevos de la capacidad de catálogo, sin alterar las tres specs vigentes.

## Impact

- Dominio: `model.py`, `violations.py` (solo nuevos códigos), paquete nuevo `catalog/`, reglas nuevas de nombres/DNI y parámetro `subject` en `rules/duration.py`. Los módulos de agenda, `Ok.appointment` y los mensajes existentes de duración/referencias conservan sus contratos; catálogo tiene un resultado separado.
- Aplicación: nuevo `backend/app/demo_data.py`, sin I/O, secretos ni import desde el dominio.
- Tests del apply: nuevos tests de catálogo, reglas y demo_data; ampliación de `test_model.py` y `test_violations.py`; migración mecánica de constructores de `Service`/`Patient` en los tests existentes y el ejemplo de `backend/README.md`.
- Documentación: `backend/README.md`, `docs/evidencias/{explore,verify,pytest,mypy}-C-09.*`; KB 04 y SU-12 de KB 09 se aclaran en este propose. Artefactos bajo `openspec/changes/catalogo-y-pacientes-dominio/`.
- Dependencia C-02 cumplida; se parte del dominio actual después de C-08. Gobernanza BAJO, sin punto de control. No cambia ningún esquema de BD, endpoint ni dependencia.
