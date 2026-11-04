# Spec Delta

## ADDED Requirements

### Requirement: Persistencia de catálogos y pacientes
La base SHALL persistir `Professional`, `Chair`, `Service` y `Patient` con ids UUID nativos y los campos definidos por el modelo de datos. `Professional` SHALL incluir `license_number` nullable solo en persistencia; `Patient` SHALL carecer de campos clínicos.

#### Scenario: Filas de catálogo y paciente
- **WHEN** se insertan entidades válidas de las cuatro clases
- **THEN** se almacenan sus ids, nombres, datos propios y estado, y una lectura devuelve el tipo correspondiente del dominio

#### Scenario: Matrícula fuera del dominio
- **WHEN** se lee un profesional con matrícula persistida
- **THEN** el tipo `Professional` devuelto conserva solo `id`, `full_name` y `active`

### Requirement: Unicidad persistente de nombres normalizados
La base SHALL conservar el nombre original y una representación normalizada de cada sillón y prestación, y SHALL impedir duplicados por esa representación. Los nombres de profesionales y pacientes NO SHALL ser únicos.

#### Scenario: Duplicado de sillón con espacios y mayúsculas
- **GIVEN** un sillón existente llamado `Sillón 1`
- **WHEN** se intenta guardar `  SILLÓN   1  `
- **THEN** el alta se rechaza como `DUPLICATE_NAME` con el mismo mensaje definido por C-09

#### Scenario: Tildes significativas
- **GIVEN** una prestación existente llamada `Extracción`
- **WHEN** se intenta guardar `Extraccion`
- **THEN** la segunda prestación no se rechaza por nombre duplicado

#### Scenario: Nombre repetido permitido
- **GIVEN** un profesional o paciente existente
- **WHEN** se guarda otra entidad de la misma clase con el mismo nombre y una clave distinta
- **THEN** el alta se acepta si las demás validaciones son correctas

### Requirement: Persistencia normalizada y única del DNI
El DNI SHALL almacenarse como texto de 7 u 8 dígitos, sin puntos ni espacios, con unicidad persistente y una restricción de base explícitamente nombrada que rechace otros formatos. Un conflicto concurrente SHALL producir `DUPLICATE_DNI` con el mensaje de C-09.

#### Scenario: DNI con formato de entrada
- **WHEN** se valida y guarda un paciente con DNI `30.111.222`
- **THEN** la fila contiene `30111222` y una lectura devuelve ese valor normalizado

#### Scenario: DNI duplicado
- **GIVEN** un paciente existente con DNI `30111222`
- **WHEN** se intenta guardar otro paciente con el mismo DNI normalizado
- **THEN** el alta se rechaza con una sola `DUPLICATE_DNI` y el mensaje de C-09

#### Scenario: DNI inválido por acceso persistente
- **WHEN** una inserción intenta guardar un DNI que no tiene 7 u 8 dígitos
- **THEN** la restricción de la base rechaza la fila y no se guarda un paciente parcial

### Requirement: Repositorios tipados de catálogos y pacientes
Los repositorios SHALL recibir y devolver únicamente tipos del dominio y SHALL usar consultas parametrizadas. Catálogos SHALL soportar alta, desactivación, reactivación, obtención por id y listado; pacientes SHALL soportar alta, obtención por id y listado.

#### Scenario: Alta validada antes de guardar
- **WHEN** una candidata de catálogo o paciente falla una validación de C-09
- **THEN** el repositorio devuelve el rechazo tipado y no crea una fila

#### Scenario: Lectura y listado
- **WHEN** se solicita una entidad por id o se lista una colección
- **THEN** se devuelven tipos del dominio, no modelos ORM, con los valores persistidos

#### Scenario: Activación idempotente
- **WHEN** se desactiva o reactiva dos veces un profesional, sillón o prestación
- **THEN** el resultado conserva el estado solicitado, no modifica otros campos y no genera una segunda violación

### Requirement: Seed ficticio e idempotente
El seed SHALL cargar tres profesionales, tres sillones, cinco prestaciones y cinco pacientes ficticios con ids fijos, y SHALL insertar solo entidades faltantes por id. No SHALL actualizar ni borrar filas existentes, ni SHALL ejecutarse automáticamente al iniciar la aplicación.

#### Scenario: Primera ejecución del seed
- **WHEN** se ejecuta el comando manual del seed sobre la base migrada
- **THEN** quedan disponibles exactamente los datos ficticios definidos para C-15, incluidas matrículas ficticias de persistencia

#### Scenario: Segunda ejecución del seed
- **WHEN** se ejecuta nuevamente el mismo seed sin limpiar la base
- **THEN** los conteos de las cuatro tablas no aumentan y los datos existentes no se actualizan ni borran

### Requirement: Integración aislada de la persistencia
Los tests de persistencia SHALL usar exclusivamente `<POSTGRES_DB>_test`, revertir la transacción de cada test y dejar la base de integración en la revisión Alembic `head` después de verificar upgrade y downgrade.

#### Scenario: Test sin contaminación
- **WHEN** un test inserta entidades y termina
- **THEN** otro test comienza sin observar esas filas

#### Scenario: Ciclo de la migración de catálogos
- **WHEN** se ejecuta `upgrade head`, `downgrade base` y `upgrade head`
- **THEN** las cuatro tablas aparecen y desaparecen según corresponda, y la base termina en `20261103_02_catalogos_y_pacientes`

#### Scenario: Violación de índice bajo concurrencia
- **WHEN** dos altas concurrentes intentan guardar el mismo nombre normalizado o DNI
- **THEN** una alta se confirma y la otra se traduce al rechazo de dominio correspondiente, sin ocultar errores de otra naturaleza
