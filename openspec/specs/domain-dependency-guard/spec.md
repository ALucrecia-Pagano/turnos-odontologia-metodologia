# domain-dependency-guard Specification

## Purpose

Garantizar, con una verificación automática que corre en la suite de tests, que el paquete de dominio del backend (`app.domain`) solo depende de una lista permitida explícita de módulos, para que las reglas de agenda sigan siendo Python puro, sin frameworks, sin I/O y sin depender de otras capas de `app`. Además, que ningún módulo del dominio lee el reloj del sistema (`datetime.now`, `datetime.utcnow`, `datetime.today`, `date.today`, con alias o por el módulo `datetime`): el momento actual se inyecta. La verificación analiza el código con `ast`, así que solo detecta nombres estáticos; los accesos dinámicos (`getattr`, asignar la clase a otra variable) no se detectan y es una limitación conocida. Convenciones: "la guardia de imports" es la verificación de la lista permitida; "la guardia del reloj" es la verificación de accesos al reloj. El módulo `time` queda cubierto por la guardia de imports, porque no está en la lista permitida.

## Requirements

### Requirement: Lista permitida de dependencias del dominio
Todo import de un módulo de `app/domain` SHALL estar permitido solo si cumple una de estas condiciones: es relativo (`from . import x`, `from .rules import y`); su primer segmento es `__future__`, `collections`, `dataclasses`, `datetime`, `enum`, `typing`, `uuid`, `zoneinfo` o `tzdata`; o es un import absoluto de `app.domain` o de un submódulo `app.domain.*`. Cualquier otro import MUST reportarse como violación.

#### Scenario: Import de un módulo de la biblioteca estándar permitido
- **WHEN** un módulo del dominio contiene `import datetime`
- **THEN** la guardia no reporta violaciones para ese import

#### Scenario: Import del tipo de identificador
- **WHEN** un módulo del dominio contiene `import uuid` o `from uuid import UUID`
- **THEN** la guardia no reporta violaciones para esos imports

#### Scenario: Import relativo a un módulo propio
- **WHEN** un módulo del dominio contiene `from . import model`
- **THEN** la guardia no reporta violaciones para ese import

#### Scenario: Import absoluto de un submódulo del propio dominio
- **WHEN** un módulo del dominio contiene `from app.domain.model import Appointment`
- **THEN** la guardia no reporta violaciones para ese import

#### Scenario: Import de un framework
- **WHEN** un módulo del dominio contiene `import fastapi`
- **THEN** la guardia reporta una violación con el módulo `fastapi`

#### Scenario: Import desde un submódulo de un paquete no permitido
- **WHEN** un módulo del dominio contiene `from sqlalchemy.orm import Session`
- **THEN** la guardia reporta una violación con el módulo `sqlalchemy.orm`

#### Scenario: Módulo de I/O de la biblioteca estándar
- **WHEN** un módulo del dominio contiene `import os` o `from pathlib import Path`
- **THEN** la guardia reporta una violación por cada uno, porque `os` y `pathlib` no están en la lista permitida

#### Scenario: Import de otra capa de la aplicación
- **WHEN** un módulo del dominio contiene `from app.api import routers` o `import app.db`
- **THEN** la guardia reporta una violación por cada uno, porque solo `app.domain` y sus submódulos están permitidos dentro de `app`

#### Scenario: Import del paquete raíz de la aplicación
- **WHEN** un módulo del dominio contiene `from app import domain`
- **THEN** la guardia reporta una violación con el módulo `app`, porque el módulo importado no es `app.domain` ni un submódulo suyo

### Requirement: Comparación por primer segmento exacto
La pertenencia a la lista permitida SHALL decidirse comparando el primer segmento del nombre punteado del módulo con cada entrada, por igualdad exacta y nunca por prefijo de texto. Un módulo cuyo nombre solo empieza con el texto de una entrada (permitida o no) MUST tratarse como un módulo distinto.

#### Scenario: Paquete cuyo nombre empieza como un framework
- **WHEN** un módulo del dominio contiene `import fastapi_utils`
- **THEN** la guardia reporta exactamente una violación cuyo módulo es `fastapi_utils` (no `fastapi`), porque `fastapi_utils` no está en la lista permitida

#### Scenario: Paquete cuyo nombre empieza como un módulo permitido
- **WHEN** un módulo del dominio contiene `import datetime_utils`
- **THEN** la guardia reporta una violación con el módulo `datetime_utils`, aunque `datetime` esté permitido

### Requirement: Cobertura de todos los imports estáticos
La guardia SHALL analizar el código fuente de todos los archivos `.py` bajo `app/domain`, incluidos los subpaquetes, y SHALL considerar cada sentencia `import` y `from ... import` del archivo, esté en el nivel del módulo, dentro de una función o dentro de un bloque condicional.

#### Scenario: Import dentro de una función
- **WHEN** un módulo del dominio define una función cuyo cuerpo contiene `import redis`
- **THEN** la guardia reporta una violación con el módulo `redis`

#### Scenario: Import en un subpaquete
- **WHEN** un archivo `rules/overlap.py` dentro del dominio contiene `import pydantic`
- **THEN** la guardia reporta una violación que identifica ese archivo

#### Scenario: Varios imports ofensivos en distintos archivos
- **WHEN** dos módulos del dominio contienen, cada uno, un import no permitido
- **THEN** la guardia reporta las dos violaciones, no solo la primera

### Requirement: Reporte identificable de cada violación
Cada violación SHALL identificar el archivo del dominio que la contiene, la línea del import y el nombre del módulo importado, y la falla del test que corre sobre el dominio real MUST mostrar esa información para todas las violaciones encontradas.

#### Scenario: Violación con archivo, línea y módulo
- **WHEN** el archivo `model.py` del dominio tiene `import fastapi` en su línea 3
- **THEN** la violación reportada identifica `model.py`, la línea 3 y el módulo `fastapi`

### Requirement: El dominio real cumple la lista permitida
La suite de tests del backend SHALL incluir una verificación que aplique la guardia al directorio `app/domain` real del repositorio y falle si encuentra al menos una violación.

#### Scenario: Dominio limpio
- **WHEN** se corre la suite de tests y ningún módulo de `app/domain` importa algo fuera de la lista permitida
- **THEN** la verificación pasa

#### Scenario: Dominio con un import prohibido
- **WHEN** se corre la suite de tests y un módulo de `app/domain` importa `sqlalchemy`
- **THEN** la verificación falla y su mensaje nombra el archivo y el import ofensivo

### Requirement: Limitación de imports dinámicos
La guardia SHALL limitarse a imports estáticos. Los imports dinámicos (`importlib.import_module("...")`, `__import__("...")`) no se detectan; esta limitación MUST quedar documentada en el diseño y en el propio helper.

#### Scenario: Import dinámico no detectado
- **WHEN** un módulo del dominio contiene `__import__("fastapi")` sin ninguna sentencia `import` de `fastapi`
- **THEN** la guardia no reporta violaciones por esa llamada (limitación conocida)

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
