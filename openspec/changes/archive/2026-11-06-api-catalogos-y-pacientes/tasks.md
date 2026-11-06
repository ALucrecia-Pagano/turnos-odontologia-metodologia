# Tasks

## 1. Dominio puro para validación de edición

- [x] 1.1 RED + GREEN: Escribir tests unitarios en RED para validación de edición de profesionales (conservando propio nombre) y sillones (conservando propio nombre 200 y con nombre de otro 409) con exclusión del propio identificador (`docs/evidencias/red-C-20/1.1.txt`) e implementar funciones puras en `app/domain/catalog/update.py`.
- [x] 1.2 RED + GREEN: Escribir tests unitarios en RED para validación de edición de prestaciones (conservando propio nombre 200 y con nombre de otra 409) y pacientes (conservando propio DNI 200 y con DNI de otro 409) con exclusión del propio identificador (`docs/evidencias/red-C-20/1.2.txt`) e implementar funciones puras en `app/domain/catalog/update.py`.

## 2. Repositorios de persistencia y soporte de matrícula

- [x] 2.1 RED + GREEN: Escribir tests de integración en RED para actualización y soporte de `license_number` en `ProfessionalRepository` y actualización de `ChairRepository`, retornando `None` ante identificadores inexistentes (`docs/evidencias/red-C-20/2.1.txt`) e implementarlos en `app/repositories/catalog.py`.
- [x] 2.2 RED + GREEN: Escribir tests de integración en RED para actualización en `ServiceRepository`, actualización y búsqueda textual en `PatientRepository` (nombre con tilde exacta insensible a mayúsculas y prefijo numérico de DNI), y filtros `active=true` y `active=false` con orden alfabético (`docs/evidencias/red-C-20/2.2.txt`) e implementarlos en `app/repositories/catalog.py` y `patients.py`.

## 3. Servicios de aplicación con transaccionalidad explícita

- [x] 3.1 RED + GREEN: Escribir tests de integración en RED para `services/catalog.py` (alta, edición, desactivación, reactivación, listado sin filtro o con `active`, detalle, y 404 ante inexistentes en lectura y escritura con `auto_commit=True`) (`docs/evidencias/red-C-20/3.1.txt`) e implementar el servicio.
- [x] 3.2 RED + GREEN: Escribir tests de integración en RED para `services/patients.py` (alta, edición, listado con búsqueda por nombre y prefijo de DNI, detalle, y 404 ante inexistentes con `auto_commit=True`) (`docs/evidencias/red-C-20/3.2.txt`) e implementar el servicio.

## 4. Esquemas Pydantic y manejo de error 404 unificado

- [x] 4.1 RED + GREEN: Escribir tests unitarios en RED para esquemas de entrada y salida en `camelCase` con `extra="forbid"` y campo `licenseNumber` (`docs/evidencias/red-C-20/4.1.txt`) e implementarlos en `app/api/schemas.py`.
- [x] 4.2 RED + GREEN: Escribir tests en RED para excepción `NotFoundError` con status 404 y cuerpo unificado `{ "code": "NOT_FOUND", "message": "<recurso> no encontrado." }` aplicable a lecturas y escrituras (`docs/evidencias/red-C-20/4.2.txt`) e implementar el manejador en `app/api/errors.py`.

## 5. Routers de API y matriz RBAC

- [x] 5.1 RED + GREEN: Escribir tests de integración en RED para `/api/professionals` (alta 201, edición 200, conservando nombre 200, desactivación 200, reactivación 200, listado alfabético sin filtro o con active, lectura permitida para recepción y odontólogo en 200, detalle 200, 404 en inexistente para detalle, edición, desactivación y reactivación, 401 sin token, 403 por rol, 422 nombre vacío, 400 malformado) (`docs/evidencias/red-C-20/5.1.txt`) e implementar `app/api/professionals.py`.
- [x] 5.2 RED + GREEN: Escribir tests de integración en RED para `/api/chairs` (alta 201, edición 200, conservando nombre 200, nombre duplicado de otro 409, desactivación 200, reactivación 200, listado sin filtro, con active=true y active=false, lectura permitida para recepción y odontólogo en 200, detalle 200, 404 en inexistente para detalle, edición, desactivación y reactivación, 401 sin token, 403 por rol, 422 nombre vacío, 400 malformado) (`docs/evidencias/red-C-20/5.2.txt`) e implementar `app/api/chairs.py`.
- [x] 5.3 RED + GREEN: Escribir tests de integración en RED para `/api/services` (alta 201, edición 200, conservando nombre 200, nombre duplicado de otra 409, desactivación 200, reactivación 200, listado alfabético sin filtro o con active, lectura permitida para recepción y odontólogo en 200, detalle 200, 404 en inexistente para detalle, edición, desactivación y reactivación, 401 sin token, 403 por rol, duración inválida 422, nombre vacío 422, 400 malformado) (`docs/evidencias/red-C-20/5.3.txt`) e implementar `app/api/services.py`.
- [x] 5.4 RED + GREEN: Escribir tests de integración en RED para `/api/patients` (alta 201 por recepción y admin, edición 200, conservando DNI 200, DNI de otro 409, búsqueda por parte del nombre con tilde 200, búsqueda sin tilde no encuentra 200, búsqueda por inicio de DNI 200, lectura permitida para odontólogo en 200, detalle 200, 404 en inexistente para detalle y edición, 401 sin token, 403 para odontólogo en alta y edición, 404 en deactivate, 405 en delete, DNI inválido 422, nombre vacío 422, 400 malformado) (`docs/evidencias/red-C-20/5.4.txt`) e implementar `app/api/patients.py` e incluir los 4 routers en `main.py`.

## 6. Verificación integral, mutaciones y evidencias

- [x] 6.1 Verificar documentación Swagger UI (`/api/docs`), contratos OpenAPI y guardianes de ruta (`test_route_guards.py`) asegurando que ninguna ruta carezca de celda RBAC ni de documentación de error 404.
- [x] 6.2 Construir y ejecutar el script `mutaciones-C-20.py` (formato de `mutaciones-C-19.py`) generando `docs/evidencias/mutaciones-C-20.txt` comprobando que cada mutación hace fallar su test.
- [x] 6.3 Ejecutar suite completa (`pytest`, `pytest -m integration`, `mypy --strict app tests`) generando `pytest-C-20.txt`, `pytest-integration-C-20.txt`, `mypy-C-20.txt` y redactar `docs/evidencias/verify-C-20.md` con los 108 escenarios comprobados con `pytest --collect-only`.
