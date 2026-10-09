# Proposal

## Why

El diferencial del producto es que la agenda **rechace** todo turno que pise a otro del mismo profesional o del mismo sillón. El Discovery muestra que es el vacío más claro del mercado: "ningún sistema comprueba un rechazo estricto de solapamientos por profesional y por sillón específico" (`docs/discovery/informe-discovery.md` §C.3.1 y §C.4.1). Odonthia, el competidor mejor documentado, solo controla que un profesional no esté en dos lugares a la vez, trata los sillones como una cantidad por sede y, en la agenda interna, "te AVISA pero no te frena": "el botón de forzar el sobreturno sigue estando" (`docs/discovery/sources/odonthia.md`, verificado a mano el 2026-10-06). Por eso el Discovery fija este change como el primero del MVP (§D.3, "Primer change": crear un turno sin solapamientos por profesional y por sillón, como lógica de dominio pura con tests por escenario) y la decisión DD-09 lo acota.

Es el change evaluado del TP porque es chico, terminable y verificable: sus reglas (intervalos semiabiertos, estados que ocupan agenda, duración por prestación) se expresan como escenarios Dado/Cuando/Entonces que se convierten uno a uno en tests de pytest, sin API, base de datos ni interfaz. C-01 ya dejó el paquete `app.domain`, pytest, `mypy --strict` y la guardia de dependencias, así que ahora se puede escribir la primera regla con Strict TDD.

## What Changes

- **Modelo del dominio** en `backend/app/domain`: turno (`Appointment`), prestación (`Service`, con duración por defecto) y estado del turno (`AppointmentStatus`: `reservado`, `confirmado`, `atendido`, `ausente`, `cancelado`). Los ids son `uuid.UUID`, siempre recibidos del llamador: el dominio nunca los genera. Los instantes son `datetime` con zona: si el valor no tiene zona (*naive*) se rechaza como error de programación (`ValueError`), y si está en otra zona se normaliza a UTC.
- **Violaciones y resultado tipado**: códigos estables `PROFESSIONAL_OVERLAP`, `CHAIR_OVERLAP` e `INVALID_DURATION`. Cada violación lleva código, mensaje mínimo en español y, si corresponde, el id del turno con el que choca. El resultado es `Ok` (con el turno nuevo) o `Rejected` (con la lista de violaciones). Las reglas de negocio no lanzan excepciones.
- **Intervalos semiabiertos** `[inicio, fin)` con su función de solapamiento (DD-07). Dos turnos consecutivos (uno termina cuando empieza el otro) no se solapan.
- **Reglas**: solapamiento por profesional (RN-AG-01) y por sillón (RN-AG-02). Los turnos `cancelado` y `ausente` no ocupan agenda (RN-AG-08). El propio dominio filtra los turnos recibidos por profesional, por sillón y por estado. Se informa una violación por cada turno que choca, ordenadas: primero las de profesional, después las de sillón (RN-AG-12), y cada grupo por inicio del turno con el que choca.
- **Duración** (RN-AG-07 y la parte mínima de RN-AG-09): se usa la duración explícita o, si no viene, la de la prestación. `fin = inicio + duración`. Una duración efectiva `<= 0` produce `INVALID_DURATION` y, como no existe un intervalo válido, en ese caso no se evalúan los solapamientos.
- **Punto de entrada** `validate_new_appointment`: devuelve `Ok` con el turno en estado `reservado` (RN-TU-01) o `Rejected` con todas las violaciones.
- **Guardia de dependencias**: se agrega `uuid` a la lista permitida del dominio (`DOMAIN_ALLOWED_MODULES`). El dominio solo lo usa como tipo.

### Fuera de alcance

- Horario de atención, bloqueos, turnos en el pasado (y por eso no se recibe `now` todavía), múltiplo de 5 minutos y máximo de 480 minutos, referencias inexistentes o inactivas, medianoche, y el texto completo de los mensajes con nombres y rango horario local (C-03 a C-08).
- Reprogramación y exclusión del propio turno (`exclude_id`, RN-TU-03) → C-11. Historial de estados → C-12.
- API, persistencia, JWT y UI.

## Capabilities

### New Capabilities
- `appointment-scheduling`: reglas del dominio para dar un turno nuevo: duración (explícita o de la prestación), intervalo semiabierto, rechazo por solapamiento de profesional y de sillón según los estados que ocupan agenda, rechazo de duración no positiva, resultado tipado con todas las violaciones ordenadas e invariantes de los instantes (con zona y normalizados a UTC).

### Modified Capabilities
- `domain-dependency-guard`: el requisito "Lista permitida de dependencias del dominio" incorpora `uuid` a los módulos permitidos.

## Impact

- **Código nuevo** en `backend/app/domain/`: `model.py`, `violations.py`, `intervals.py`, `rules/` (`overlap.py`, `duration.py`) y `appointment/` (`validate_new_appointment`). Tests nuevos en `backend/tests/domain/`.
- **Archivos modificados**: `backend/tests/domain/import_guard.py` (allowlist + `uuid`), `backend/tests/domain/test_import_guard.py` (caso `import uuid`), `backend/README.md` (estructura del dominio).
- **Dependencias**: ninguna nueva (`uuid` es biblioteca estándar).
- **Governance**: ALTO. Es el modelo central del que dependen los demás changes, así que hay un punto de control obligatorio: la autora revisa los tipos y la API pública antes de que se implementen las reglas.
