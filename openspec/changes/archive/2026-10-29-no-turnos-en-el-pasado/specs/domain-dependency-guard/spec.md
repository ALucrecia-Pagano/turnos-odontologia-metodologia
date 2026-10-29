# Spec Delta

Convenciones de este delta: "la guardia del reloj" es la verificación nueva de este requisito; "la guardia de imports" es la de los requisitos existentes (lista permitida). En cada escenario, el código citado está en un módulo de `app/domain`.

## ADDED Requirements

### Requirement: Sin reloj global en el dominio
Ningún módulo de `app/domain` SHALL leer el reloj del sistema (RN-GL-04; US-005 CA-4). La guardia del reloj SHALL analizar el código de todos sus `.py` y reportar todo acceso, llamado o no, a `now`, `utcnow` o `today` de la clase `datetime` y a `today` de la clase `date`, directo, por el módulo `datetime` o con alias, y todo `from datetime import *`, con archivo, línea y la expresión. El módulo `time` lo cubre la guardia de imports. Solo detecta nombres estáticos.

#### Scenario: Llamada a datetime.now
- **WHEN** un módulo del dominio contiene `from datetime import datetime` y una línea con `datetime.now(timezone.utc)`
- **THEN** la guardia del reloj reporta un acceso al reloj con la expresión `datetime.now`

#### Scenario: Llamadas a datetime.utcnow y datetime.today
- **WHEN** un módulo del dominio contiene `from datetime import datetime` y `datetime.utcnow()` (primer caso) o `datetime.today()` (segundo caso)
- **THEN** en cada caso la guardia del reloj reporta un acceso al reloj, con la expresión `datetime.utcnow` o `datetime.today` respectivamente

#### Scenario: Llamada a date.today
- **WHEN** un módulo del dominio contiene `from datetime import date` y `date.today()`
- **THEN** la guardia del reloj reporta un acceso al reloj con la expresión `date.today`

#### Scenario: Llamada por el módulo datetime
- **WHEN** un módulo del dominio contiene `import datetime` y `datetime.datetime.now()` (primer caso) o `datetime.date.today()` (segundo caso)
- **THEN** en cada caso la guardia del reloj reporta un acceso al reloj, con la expresión `datetime.datetime.now` o `datetime.date.today` respectivamente

#### Scenario: Llamada con alias
- **WHEN** un módulo del dominio contiene `import datetime as dt` y `dt.datetime.now()` (primer caso) o `from datetime import datetime as D` y `D.now()` (segundo caso)
- **THEN** en cada caso la guardia del reloj reporta un acceso al reloj, con la expresión `dt.datetime.now` o `D.now` respectivamente

#### Scenario: Referencia al reloj sin llamarlo
- **WHEN** un módulo del dominio contiene `from datetime import datetime` y `reloj = datetime.now`, sin llamarlo
- **THEN** la guardia del reloj reporta un acceso al reloj con la expresión `datetime.now`

#### Scenario: Llamada dentro de una función
- **WHEN** un módulo del dominio contiene `from datetime import datetime` y una función cuyo cuerpo llama a `datetime.now()`
- **THEN** la guardia del reloj reporta un acceso al reloj con la expresión `datetime.now`

#### Scenario: Import con asterisco del módulo datetime
- **WHEN** un módulo del dominio contiene `from datetime import *`
- **THEN** la guardia del reloj reporta ese import, porque no se puede saber qué nombres trae

#### Scenario: Momento actual inyectado
- **WHEN** un módulo del dominio contiene `from datetime import datetime` y lee `context.now` (primer caso) o recibe un parámetro `now` y lo compara con el inicio (segundo caso)
- **THEN** en ambos casos la guardia del reloj no reporta nada, porque `context` y `now` no son la clase ni el módulo `datetime`

#### Scenario: Construcción de instantes y duraciones
- **WHEN** un módulo del dominio contiene `from datetime import datetime, timedelta, timezone` y `datetime(2026, 10, 20, tzinfo=timezone.utc)` (primer caso) o `timedelta(minutes=30)` (segundo caso)
- **THEN** en ambos casos la guardia del reloj no reporta nada

#### Scenario: La palabra now en un docstring
- **WHEN** un módulo del dominio tiene un docstring que dice "`now` se inyecta; nunca `datetime.now()`"
- **THEN** la guardia del reloj no reporta nada, porque analiza código y no texto

#### Scenario: Reloj del módulo time
- **WHEN** un módulo del dominio contiene `import time` (primer caso) o `from time import time as t` (segundo caso)
- **THEN** en ambos casos la guardia de imports reporta una violación con el módulo `time`, porque `time` no está en la lista permitida

#### Scenario: Accesos dinámicos no detectados
- **WHEN** un módulo del dominio contiene `from datetime import datetime` y `getattr(datetime, "now")()` (primer caso) o `d = datetime` seguido de `d.now()` (segundo caso)
- **THEN** en ambos casos la guardia del reloj no reporta nada (limitación conocida y documentada)

#### Scenario: Reporte con archivo y línea
- **WHEN** el archivo `rules/past.py` del dominio tiene `datetime.now()` en su línea 4, con `from datetime import datetime` en la línea 1
- **THEN** el acceso reportado identifica `rules/past.py`, la línea 4 y la expresión `datetime.now`
- **AND** el mensaje de la falla es una línea por acceso, con la ruta, la línea y la expresión

#### Scenario: Varios accesos en orden de línea
- **WHEN** un módulo del dominio contiene `from datetime import datetime`, una función cuyo cuerpo llama a `datetime.now()` en la línea 5 y `datetime.utcnow()` a nivel de módulo en la línea 8 (primer caso), o `datetime.now()` en la línea 3 y `datetime.today()` en la línea 4 (segundo caso)
- **THEN** la guardia del reloj reporta los accesos ordenados por línea: `datetime.now` (5) y `datetime.utcnow` (8) en el primer caso, aunque el primero esté dentro de una función; `datetime.now` (3) y `datetime.today` (4) en el segundo

#### Scenario: Dominio real sin reloj global
- **WHEN** se corre la suite de tests sobre el `app/domain` real del repositorio
- **THEN** la guardia del reloj no reporta ningún acceso y la verificación pasa; si encontrara alguno, la verificación falla y su mensaje nombra el archivo, la línea y la expresión
