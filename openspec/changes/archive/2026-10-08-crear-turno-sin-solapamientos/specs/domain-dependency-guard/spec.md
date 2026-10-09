# Spec Delta

## MODIFIED Requirements

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
