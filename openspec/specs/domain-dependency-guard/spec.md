# domain-dependency-guard Specification

## Purpose

Garantizar, con una verificación automática que corre en la suite de tests, que el paquete de dominio del backend (`app.domain`) solo depende de una lista permitida explícita de módulos, para que las reglas de agenda sigan siendo Python puro, sin frameworks, sin I/O y sin depender de otras capas de `app`.

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
