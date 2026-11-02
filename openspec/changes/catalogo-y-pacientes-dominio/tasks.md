# Tasks

Gobernanza BAJO (D13), sin punto de control. Ejecutar en orden, una conducta por vez. Antes de modificar archivos existentes, correr su red de seguridad; si falla un test previo sin explicación, detener y reportar. Cada RED se ejecuta y se anota con su salida; no se pasa a GREEN antes de confirmar el fallo esperado. Cada triangulación agrega un caso y ejecuta, generalizando lo mínimo. Si ya pasa, comprobar sensibilidad con la mutación indicada, anotar y restaurar. No escribir todos los tests de un grupo de una vez. Al refactorizar, ejecutar después de cada cambio. No mocks, patch, monkeypatch, freezegun, `Any` ni `type: ignore`.

Seams: altas públicas (reglas y composición), activación pública (copias), `validate_new_appointment` (regresión), modelo/fields (contrato mínimo), demo_data/guardias (datos y aislamiento), como define design. Los tests del dominio usan literales del spec e instantes UTC fijados; no importan demo_data como fuente de expectativas. Las pruebas de reutilización de ejemplos son separadas. Cada tarea se marca únicamente cuando su verificación está completa y se conserva evidencia RED/GREEN/mutaciones.

## 1. Red de seguridad

- [ ] 1.1 Desde backend ejecutar `.venv/Scripts/python.exe -m pytest` y `.venv/Scripts/python.exe -m mypy --strict app tests`; anotar número de tests/archivos y salidas. C-08 cerró con 375/33, pero el baseline es el estado real, no ese número supuesto. No modificar producción si hay fallos preexistentes.
- [ ] 1.2 Revisar `git diff`/status y localizar todos los constructores actuales de Service y Patient, también el ejemplo de backend/README.md. Anotar la lista para la migración mecánica y confirmar que no hay trabajo ajeno que se vaya a sobrescribir.

## 2. Modelo mínimo

- [ ] 2.1 RED en `test_model.py` del escenario «Prestación con estado activo por defecto»: construir Service con id, nombre y duración sin active; comprobar los cuatro valores. Ejecutar y registrar el fallo por el campo nuevo todavía inexistente.
- [ ] 2.2 GREEN: agregar solo Service.name en el orden D8; migrar mecánicamente los constructores existentes con nombres ficticios y el ejemplo README. Ejecutar el test y suite previa/mypy; no modificar expectativas de agenda para hacerlos pasar.
- [ ] 2.3 RED de «Campos exactos del paciente» y «Opcionales de paciente ausentes», uno por vez; GREEN mínimo de Patient conforme D8. Migrar constructores existentes con nombre/DNI ficticios sin cambiar expectativas; verificar cada paso y suite/mypy. Enumerar los cinco campos exactos con `dataclasses.fields` y expectativas literales.
- [ ] 2.4 TRIANGULATE los escenarios «Construcción no rechaza datos de negocio inválidos» y «Profesional sin matrícula en el dominio». Si ya pasan, mutar temporalmente la validación del constructor y agregar un campo clínico para comprobar fallos, uno por vez; restaurar y comprobar suite verde. No agregar validaciones al modelo.
- [ ] 2.5 REFACTOR docstrings de modelo y ejemplo README para reflejar campos nuevos y que valida el alta; verificar ejemplo ejecutable y suite/mypy, con diff de migración solo mecánico en tests previos.

## 3. Resultados y códigos

- [ ] 3.1 RED del resultado separado `catalog.result.Ok` con dos tipos concretos (profesional y paciente, uno por ciclo), inspeccionando entity; GREEN mínimo del wrapper/alias tipados D1 técnico. Reutilizar Rejected; no modificar `violations.Ok`, `ValidationResult` ni código/tests existentes que usan `Ok.appointment`, sus imports o expectativas. Comprobar el contrato de agenda mediante sus tests existentes sin alterarlos; la migración mecánica D8 no cambia ese payload.
- [ ] 3.2 RED de los cuatro valores nuevos de ViolationCode; GREEN agregando solo EMPTY_NAME, DUPLICATE_NAME, INVALID_DNI y DUPLICATE_DNI. Verificar suite de violations y mypy; no cambiar códigos ni textos existentes.
- [ ] 3.3 REFACTOR documentación del resultado/códigos y aliases de imports para distinguir ambos Ok; comprobar mypy sin Any/ignore y tests de resultados verdes.

## 4. Alta de profesional y nombre obligatorio

- [ ] 4.1 RED de «Profesional válido» a través de create_professional; GREEN mínimo de alta pública y resultado. Registrar fallo/pase, incluyendo id y nombre literales.
- [ ] 4.2 RED «Nombre vacío de profesional»; GREEN mínimo con EMPTY_NAME y texto exacto usando regla pura de nombre. TRIANGULATE el profesional de nombre blanco; comprobar que falla antes de generalizar la condición, o mutar la guarda de blancos si ya pasa; restaurar.
- [ ] 4.3 TRIANGULATE «Profesional con nombre repetido permitido» y «Nombre original de profesional conservado», uno por ciclo. Si pasan de entrada, mutar el nombre devuelto para recortarlo y comprobar sensibilidad del caso de conservación, restaurar. No agregar unicidad de profesional.
- [ ] 4.4 REFACTOR regla compartible de nombre, docstrings de create_professional y documentación de alta en backend/README.md. Ejecutar suite/mypy; el resultado por nombre inválido es Rejected, no excepción.

## 5. Alta de sillón y unicidad de nombres

- [ ] 5.1 RED «Sillón válido»; GREEN mínimo create_chair. TRIANGULATE «Sillón diferente permitido»; ejecutar y comprobar colección/original sin cambios.
- [ ] 5.2 RED «Nombre vacío de sillón»; GREEN texto exacto. TRIANGULATE nombre solo de espacios y «Nombre vacío no produce duplicado» para sillón; si ya pasan mutar la guarda de duplicado para que vacío participe y comprobar fallo; restaurar.
- [ ] 5.3 RED «Nombre de sillón duplicado exacto»; GREEN comprobación contra Sequence con una DUPLICATE_NAME. TRIANGULATE «Sillón duplicado con mayúsculas y espacios»; generalizar clave normalizada D4 tras fallo. Verificar texto exacto `Ya existe un sillón con el nombre "SILLÓN 1".` para candidata `"  SILLÓN   1  "`: recortar y colapsar espacios sin cambiar mayúsculas/tildes, sin usar nombre existente ni clave con casefold. Mutar la presentación a solo strip y después a casefold, comprobar los fallos y restaurar cada mutación.
- [ ] 5.4 TRIANGULATE «Las tildes distinguen sillones», «Un existente inactivo conserva su nombre único» y «Varios existentes equivalentes producen una violación» (caso sillón), uno por ciclo. Mutaciones quitar casefold, quitar colapso y filtrar solo activos, una por vez: ejecutar tests relevantes, registrar fallos y restaurar. Verificar todos verdes.
- [ ] 5.5 REFACTOR `rules/catalog_names.py` sin alterar subject_name, docstrings de alta/normalización y README; suite/mypy verdes. Las expectativas de normalización son literales, no se calculan con el helper bajo prueba.

## 6. Alta de prestación y duración reutilizada

- [ ] 6.1 RED «Prestación válida»; GREEN mínimo create_service, conservando estado por defecto ya probado. Ejecutar test y registrar salida.
- [ ] 6.2 RED «Nombre vacío de prestación»; GREEN nombre requerido con texto exacto. TRIANGULATE blanco y vacío sin duplicado de prestación, un caso por ciclo; restaurar cualquier mutación de guarda y verificar verde.
- [ ] 6.3 RED «Nombre de prestación duplicado exacto»; GREEN composición de regla común. TRIANGULATE variante mayúsculas/espacios, Control de ortodoncia con espacios internos, tildes que distinguen y casos inactivo/varios existentes del requisito de unicidad, uno por ciclo. Verificar texto exacto `Ya existe una prestación con el nombre "CONTROL DE ORTODONCIA".` para candidata `" CONTROL   DE  ORTODONCIA "`, colapsando espacios y preservando mayúsculas/tildes. Si ya pasan, mutar la normalización al comparar solo candidato y comprobar caso existente normalizado; mutar la presentación para conservar espacios internos y comprobar fallo del mensaje; restaurar cada mutación.
- [ ] 6.4 RED «Duración fuera de la grilla» por el alta con el texto «La duración de la prestación»; GREEN componiendo check_duration con `subject="de la prestación"`, sin duplicar la lógica. Incorporar solo el parámetro `subject: str = "del turno"` en duration.py y usarlo en el sujeto del mensaje. TRIANGULATE cero/-5, 485, 487 y límites5/480, uno por ciclo, con mensajes completos literales de spec; las razones y su orden no cambian.
- [ ] 6.4a Regresión exacta de C-03 y parámetro de sujeto: agregar un test parametrizado de check_duration sin informar subject para 0, -5, 7, 485 y 487, con los cinco textos completos literales «La duración del turno» vigentes, sin editar expectativas de tests existentes. Ejecutar cada caso; si ya pasa, registrar regresión verde y mutar temporalmente el valor predeterminado a «de la prestación» para comprobar que falla; restaurar. Contrastar con el sujeto explícito «de la prestación» de 6.4; el RED de ese parámetro debe ejecutarse antes de su GREEN, y los casos de turno quedan idénticos después. Verificar suite y mypy en verde.
- [ ] 6.5 MUTACIÓN de cableado: omitir temporalmente check_duration en el alta, comprobar que fallan los casos inválidos y restaurar. Omitir `subject="de la prestación"`, comprobar fallos de textos de catálogo; mutar el valor predeterminado a «de la prestación», comprobar fallos de regresión C-03 y restaurar. Ejecutar suite verde y revisar diff de duration.py limitado al parámetro, sujeto y docstring, sin cambios de reglas ni razones.
- [ ] 6.6 REFACTOR docstrings/README de prestaciones y regla única con sujeto parametrizado; suite/mypy sin errores. Conservar mensajes exactos C-03 con el valor predeterminado y textos de catálogo con sujeto explícito. No alterar INACTIVE_REFERENCE.

## 7. Alta de paciente y DNI

- [ ] 7.1 RED «Paciente válido con DNI con puntos»; GREEN mínimo create_patient que devuelve copia con solo dígitos. TRIANGULATE «Paciente válido con DNI sin puntos»; comprobar candidata/colección intactas y opcionalesNone. Ejecutar tras cada caso.
- [ ] 7.2 RED «Nombre vacío de paciente»; GREEN texto exacto con regla compartida. TRIANGULATE nombre blanco, nombre repetido permitido y opcionales de texto libre/vacío, un caso por vez; si ya pasan, mutar el nombre aceptado para comprobar conservación, restaurar.
- [ ] 7.3 RED «DNI con guiones inválido» con mensaje completo; GREEN de regla pura en rules/dni.py. TRIANGULATE seis dígitos, nueve, letras, vacío y blanco, uno por ciclo; verificar INVALID_DNI y texto original recibido sin excepción.
- [ ] 7.4 TRIANGULATE «DNI de siete dígitos válido» y «DNI con puntos y espacios válido» con sus dos variantes. Si ya pasan, mutar límites para aceptar solo ocho dígitos y omitir eliminación de espacios, una por vez; registrar fallos y restaurar.
- [ ] 7.5 RED «DNI duplicado sin puntos»; GREEN regla de unicidad por Sequence. TRIANGULATE con/sin puntos en ambos sentidos, duplicado siete dígitos con mensaje3.111.222 y colección invertida, uno por ciclo; verificar mismo texto y una sola violación.
- [ ] 7.6 TRIANGULATE «DNI inválido no produce duplicado»; mutar temporalmente la guarda para comparar el inválido existente, comprobar que falla el test y restaurar. Mutar comparación por texto bruto y formato sin miles, una por vez; registrar fallos de equivalencia/mensaje, restaurar y suite verde.
- [ ] 7.7 REFACTOR docstrings/README del alta de pacientes, DNI y ausencia de clínica; comprobar suite/mypy. Sin nueva validación de teléfono, obra social ni excepciones por datos de usuario.

## 8. Composición completa de violaciones

- [ ] 8.1 TRIANGULATE «Nombre y DNI inválidos juntos» y «Nombre vacío y DNI duplicado», uno por ciclo; si el alta corta, registrar RED y hacer GREEN mínimo conservando orden D9. Si ya pasa, mutar a retorno tras primer error y comprobar fallo; restaurar.
- [ ] 8.2 TRIANGULATE «Prestación duplicada y duración inválida» y «Nombre vacío no oculta duración inválida», uno por ciclo, con listas completas y textos exactos. Mutar el orden para duración primero y comprobar fallos; restaurar. No evaluar duplicado del nombre vacío.
- [ ] 8.3 TRIANGULATE «Metadatos de las violaciones nuevas» para los cuatro códigos. Si ya pasa, mutar reference_kind en una violación, comprobar fallo y restaurar; no inventar ids de entidad en los campos de conflicto de agenda.
- [ ] 8.4 REFACTOR composición y docstrings de altas con orden completo; verificar suite/mypy y documentar README con ejemplo de varias violaciones; no cambiar RN-AG-12 de agenda.

## 9. Desactivar y reactivar

- [ ] 9.1 RED «Desactivar cada recurso activo» empezando por Professional; GREEN mínimo deactivate mediante dataclasses.replace. TRIANGULATE Chair y Service, uno por ciclo, verificando campos y que original sigue activo.
- [ ] 9.2 RED «Reactivar cada recurso inactivo» empezando por Professional; GREEN mínimo reactivate. TRIANGULATE Chair y Service, uno por ciclo, verificando tipo/campos y original inactivo.
- [ ] 9.3 TRIANGULATE los dos escenarios idempotentes para los tres recursos, uno por ciclo. Si ya pasan, mutar temporalmente a alternar active, comprobar fallos y restaurar; no agregar ALREADY_INACTIVE ni ALREADY_ACTIVE.
- [ ] 9.4 MUTACIÓN de copia: devolver el objeto original sin cambiar estado, comprobar fallo del caso de desactivación, restaurar. Verificar por valores originales/copia que no hay mutación interna y que no se agregó active a Patient; suite/mypy verdes.
- [ ] 9.5 REFACTOR docstrings/README de activación y sus tipos concretos. Ejecutar tests de los tres tipos y mypy; sin cast a Any ni wrapper de rechazo que no se necesita.

## 10. Integración con agenda existente

- [ ] 10.1 TRIANGULATE «Desactivar no modifica turnos existentes» con los tres recursos, usando valores literales del turno antes/después. Si pasa de entrada, registrarlo honestamente como regresión verde: la operación no recibe ni toca turnos y no requiere producción nueva. No falsear RED cambiando expectativas ni agregar parámetro turnos. La sensibilidad de la copia se verifica en 9.4 y el efecto real sobre agenda en 10.2; ejecutar también tests de agenda previos.
- [ ] 10.2 RED de «Turno nuevo con profesional desactivado» por la seam validate_new_appointment después de deactivate. Si pasa de entrada por comportamiento vigente, mutar temporalmente el resultado de deactivate a activo para comprobar fallo; restaurar. TRIANGULATE sillón/prestación desactivados con mensajes exactos existentes, uno por ciclo.
- [ ] 10.3 TRIANGULATE «Turno nuevo después de reactivar» y verificar payload Ok.appointment sin cambiar código/tests existentes que lo usan. REFACTOR documentación de integración; comprobar diff vacío de rules/references.py y reglas de agenda salvo el parámetro de sujeto de duration.py autorizado en D2, con textos C-03 idénticos, y ejecutar suite/mypy. Todas las mutaciones temporales deben estar restauradas.

## 11. Demo data y aislamiento

- [ ] 11.1 RED «Catálogo y paciente ficticios disponibles» por la importación pública de app.demo_data; GREEN mínimo de colecciones con datos ficticiosD10 y UUID literales, fuera del dominio. Sin seed ejecutable ni secretos. Registrar fallo y pase.
- [ ] 11.2 TRIANGULATE «Ejemplos válidos por las altas», una entidad por ciclo con colección vacía y original intacto. Si ya pasa, mutar duración o DNI de un ejemplo, comprobar fallo por la seam pública y restaurar. Los tests de reglas siguen usando literales, no demo_data.
- [ ] 11.3 TRIANGULATE «El dominio no importa demo_data» y «Dominio sin reloj global ni generación de identificadores». Usar guardias existentes; mutación temporal import app.demo_data dentro de catálogo debe fallar y se restaura. Ejecutar guardias reales y revisión de UUID/I/O sin coincidencias nuevas.
- [ ] 11.4 REFACTOR docstring de demo_data y README con ejemplos ficticios/reutilización y sentido único de dependencias. Ejecutar tests/mypy; ningún import del dominio depende de demo_data. Sin campos clínicos ni contraseñas.

## 12. Verificación integral y evidencias

- [ ] 12.1 Ejecutar pytest -v completo desde backend, con más casos que baseline y los escenarios C-01 a C-08 conservados; guardar salida completa en docs/evidencias/pytest-C-09.txt y anotar resultado real.
- [ ] 12.2 Ejecutar mypy --strict app tests desde backend y guardar salida completa en docs/evidencias/mypy-C-09.txt; cero errores y sin type: ignore ni Any.
- [ ] 12.3 Trazar todos los escenarios de specs/catalog-and-patients/spec.md (63 encabezados, incluyendo todas las variantes de cada escenario parametrizado) a tests PASSED concretos en verify-C-09.md; comparar conteo real y no omitir los que ya pasaban.
- [ ] 12.4 Revisar pureza integral con find_forbidden_imports=[] y find_global_clock_calls=[] sobre dominio real; búsqueda de uuid1/uuid4, Any, os.environ/getenv, unicodedata y raises nuevos sin reglas de negocio lanzadas. Verificar ausencia de demo_data imports en dominio y Patient exactamente cinco campos.
- [ ] 12.5 Revisar cumplimiento KB04, SU-12, RN-PA-01/02, RN-AG-09 y US-020/021/022, sin cambiar estados del roadmap ni specs principales en apply. Comparar mensajes exactos nuevos, regresión literal de duración de C-03, presentación de DUPLICATE_NAME con espacios colapsados y references.py sin cambios; verificar diff de duration.py limitado al parámetro de sujeto y ningún cambio de contrato ni consumidores de Ok.appointment.
- [ ] 12.6 Ejecutar openspec validate catalogo-y-pacientes-dominio --strict desde raíz y guardar resultado en verify-C-09.md; debe ser válido sin dependencias nuevas.
- [ ] 12.7 Completar docs/evidencias/verify-C-09.md con formato C-08: fecha/comandos/resultados, escenarios obligatorios feliz/error/borde, tabla completa63, textos exactos, evidencia SafetyNet/RED/GREEN/TRIANGULATE/REFACTOR y mutaciones con salidas/restauración, y desvíos. Registrar mismos desvíos en design.md; no inventar evidencias históricas.
- [ ] 12.8 Revisar git diff --check y git status: solo Impact+evidencias del change, sin archivos prohibidos ni cambios de otros changes, sin stage/commit/push/archive. Reportar conteo final de tareas con grep y resumen de resultados, sin archivar.
