# Spec Delta

## ADDED Requirements

### Requirement: Migraciones versionadas y configuración segura
El backend SHALL ejecutar migraciones versionadas desde `backend/` y SHALL
obtener `DATABASE_URL` de la configuración de la aplicación; ningún archivo
INI SHALL contener una URL de conexión.

#### Scenario: Configuración sin URL en alembic.ini
- **WHEN** se inspecciona la configuración y se inicia Alembic con un entorno válido
- **THEN** la URL efectiva proviene de `DATABASE_URL` cargada por la aplicación
- **AND** `alembic.ini` no contiene una URL de conexión

#### Scenario: Migración inicial
- **WHEN** se ejecuta `upgrade head` sobre una base de test vacía
- **THEN** termina sin errores y registra la revisión inicial
- **AND** no crea tablas de negocio

### Requirement: Reversibilidad de la línea de base
La línea de base SHALL poder revertirse hasta `base` sin errores y SHALL
dejar la base sin tablas de negocio.

#### Scenario: Downgrade a base
- **WHEN** se ejecuta `downgrade base` después de `upgrade head`
- **THEN** termina sin errores
- **AND** no quedan tablas de negocio

### Requirement: Aislamiento de migraciones de integración
Los tests de migraciones SHALL usar exclusivamente `<POSTGRES_DB>_test`,
nunca la base de desarrollo, y SHALL dejar la base de test en `head` al
finalizar la sesión de integración.

#### Scenario: Base de test restaurada en head
- **WHEN** la suite de migraciones ejecuta upgrade, downgrade y upgrade final
- **THEN** todas las operaciones se realizan sobre `<POSTGRES_DB>_test`
- **AND** la revisión final es `head`

### Requirement: Metadata consistente con las migraciones
La metadata declarativa SHALL usar una convención estable para constraints e
índices, y una comparación de autogenerate sobre una base migrada SHALL no
encontrar diferencias.

#### Scenario: Autogenerate vacío
- **WHEN** se compara la metadata con `MigrationContext` contra la base de
  test migrada
- **THEN** la lista de diferencias es vacía
- **AND** `alembic_version` no se interpreta como tabla de negocio

#### Scenario: Convención de nombres
- **WHEN** un test crea un constraint de ejemplo usando la metadata declarativa
- **THEN** el nombre generado respeta la convención acordada
- **AND** el test no agrega una tabla de negocio a la migración inicial

### Requirement: Separación de infraestructura y dominio
La infraestructura de migraciones SHALL permanecer fuera de
`backend/app/domain`, y el dominio SHALL poder verificarse sin importar
Alembic.

#### Scenario: Dominio sin Alembic
- **WHEN** se ejecuta la guardia de dependencias sobre `backend/app/domain`
- **THEN** no se reporta ningún import de Alembic

### Requirement: Verificación no destructiva por defecto
La ejecución de pytest sin el selector `integration` SHALL seguir excluyendo
los tests que requieren PostgreSQL, Docker o Alembic aplicado.

#### Scenario: Pytest unitario sin infraestructura
- **WHEN** se ejecuta `pytest` sin `-m integration`
- **THEN** los tests de integración no se ejecutan
- **AND** la suite no requiere Docker
