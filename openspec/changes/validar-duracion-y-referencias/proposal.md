# Proposal

## Why

C-02 dejó el núcleo de la agenda: un turno se rechaza si pisa a otro del mismo profesional o del mismo sillón, y la duración solo se controla en su parte mínima (mayor que cero). Hoy el dominio todavía acepta pedidos que no tienen sentido para el consultorio: una duración de 7 minutos o de 9 horas, un profesional dado de baja, un sillón fuera de servicio, una prestación que no existe o un paciente que nadie cargó. US-007 (CA-1 y CA-2) pide rechazar todas esas entradas para proteger la integridad de la agenda, y RN-AG-09 y RN-AG-11 son las reglas que lo dicen.

Además, con la firma actual de C-02 el dominio no puede ver una prestación inexistente: la recibe como objeto ya resuelto. Eso deja RN-AG-11 del lado de la API y rompe la regla dura de no duplicar reglas fuera del dominio. Este change corrige eso ahora, antes de que C-04 a C-08 sumen más reglas sobre la misma firma, y antes de la API (C-22), que tiene que saber qué violaciones son de validez (`422`) y cuáles de conflicto de agenda (`409`).

Depende de C-02 porque amplía su regla de duración (`rules/duration.py`), su resultado tipado (`Violation`, `ViolationCode`) y su punto de entrada `validate_new_appointment`. Las decisiones salen del explore del 2026-10-22 (`docs/evidencias/explore-C-03.md`).

## What Changes

- **Duración válida completa** (RN-AG-09, RN-DI-05 solo en la parte de la duración, SU-02): además de ser mayor que cero, la duración efectiva tiene que ser múltiplo de 5 minutos y no superar 480 minutos. Los límites quedan como constantes del módulo `rules/duration.py`. Si la duración rompe más de una condición (por ejemplo 487), se informa **una sola** `INVALID_DURATION` cuyo mensaje nombra todas las razones.
- **Referencias** (RN-AG-11, US-007 CA-2): el profesional, el sillón y la prestación tienen que existir y estar activos; el paciente tiene que existir. Códigos nuevos `UNKNOWN_REFERENCE` (no existe) e `INACTIVE_REFERENCE` (existe pero está inactivo). El paciente no tiene estado activo, así que solo puede dar `UNKNOWN_REFERENCE`.
- **Quién resuelve las referencias**: quien llama busca cada id y le pasa al dominio la entidad encontrada o `None`. El dominio decide. El pedido de turno suma `service_id`. **BREAKING** (solo interno): cambia la firma de `validate_new_appointment`; los tests de C-02 se adaptan en la llamada sin cambiar lo que verifican.
- **Modelos mínimos**: `Professional(id, active)`, `Chair(id, active)`, `Patient(id)` y `active: bool = True` en `Service`. Los nombres y el resto de los datos llegan con C-09.
- **Violación con tipo de referencia**: campo opcional `reference_kind` (paciente, profesional, sillón o prestación) para que el frontend marque el campo del formulario sin leer el texto del mensaje.
- **Dos grupos de violaciones**: primero la validez del pedido (referencias y duración), informadas todas juntas. Si hay alguna, no se evalúan los conflictos de agenda (solapamientos). Así un resultado nunca mezcla errores de validez con conflictos de agenda. Dentro del primer grupo van primero las referencias (paciente, profesional, sillón, prestación) y después la duración (RN-AG-12).

### Fuera de alcance

- Inicio del turno en la grilla de 5 minutos (parte de inicio de RN-DI-05) → C-04, porque se evalúa en hora local. Ya está anotado en `CHANGES.md`.
- Mensajes completos con nombres de profesional, sillón o prestación y rango horario local → C-08.
- Modelos completos de catálogo y pacientes (nombres, DNI, validaciones) → C-09.
- Traducción de los grupos a códigos HTTP (`422` / `409`) y carga de las entidades con repositorios → C-22 y C-23.
- Q-15 (generalizar "sillón" a un recurso genérico) **no** se aborda: el modelo mantiene `Chair`.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `appointment-scheduling`: el requisito de duración no positiva se amplía a la validez completa de la duración; se agrega el requisito de referencias existentes y activas; el alta de un turno válido exige referencias válidas; el orden de las violaciones pasa a dos grupos (validez del pedido y conflictos de agenda); el contenido de cada violación suma `reference_kind`.

## Impact

- **Código modificado** en `backend/app/domain/`: `model.py` (`Professional`, `Chair`, `Patient`, `Service.active`, `NewAppointmentRequest.service_id`, contenedor de referencias), `violations.py` (`UNKNOWN_REFERENCE`, `INACTIVE_REFERENCE`, `ReferenceKind`, `Violation.reference_kind`), `rules/duration.py` (validez completa y constantes), `appointment/validate.py` (firma nueva y dos grupos).
- **Código nuevo**: `backend/app/domain/rules/references.py`.
- **Tests**: `backend/tests/domain/test_validate_new_appointment.py` (escenarios nuevos y adaptación de la llamada en los de C-02), `test_model.py` y `test_violations.py`.
- **Documentación**: `backend/README.md` (ejemplo de uso con la firma nueva).
- **Dependencias**: ninguna nueva. La allowlist del dominio no cambia.
- **Governance**: MEDIO. Hay un punto de control antes de implementar las reglas: la autora revisa los tipos y la firma nueva.
