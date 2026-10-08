# Spec Delta

## Purpose

Proveer un proyecto Python del backend instalable y reproducible en un entorno virtual local, con una suite de pytest y un chequeo de tipos estricto, y con el paquete `app.domain` disponible para que los changes de dominio apliquen Strict TDD desde su primer test.

## ADDED Requirements

### Requirement: Proyecto instalable con dependencias declaradas
El backend SHALL ser un proyecto Python instalable en modo editable desde `backend/`, que declare compatibilidad con Python 3.12 o superior, la dependencia de runtime `tzdata` y un grupo opcional de desarrollo `dev` con pytest 8 y mypy.

#### Scenario: Instalación en un entorno virtual nuevo
- **WHEN** en un entorno virtual nuevo con Python 3.13 se instala el backend en modo editable con el grupo `dev`
- **THEN** la instalación termina sin errores y quedan disponibles `pytest`, `mypy` y `tzdata`

#### Scenario: Versión de Python declarada
- **WHEN** se consulta la metadata del proyecto instalado
- **THEN** declara `Requires-Python` igual a `>=3.12`

### Requirement: Paquete de dominio disponible
El proyecto SHALL exponer el paquete `app.domain`, importable desde el entorno virtual, que en este change no contiene lógica de negocio y que se resuelve al directorio `backend/app/domain` del repositorio.

#### Scenario: `app.domain` es un paquete
- **WHEN** se importa `app.domain` desde el entorno virtual
- **THEN** el módulo importado es un paquete (tiene ruta de búsqueda de submódulos)

#### Scenario: `app.domain` apunta al código del repositorio
- **WHEN** se importa `app.domain` desde el entorno virtual
- **THEN** su ubicación es el directorio `backend/app/domain` del repositorio, no una copia instalada en otro lugar

### Requirement: Suite de tests ejecutable
Ejecutar `pytest` desde `backend/` sin argumentos SHALL recolectar los tests de `backend/tests` y terminar en verde.

#### Scenario: Corrida de la suite
- **WHEN** se ejecuta `pytest` en `backend/` con el entorno virtual activo
- **THEN** se recolectan los tests de `tests/` y todos pasan

### Requirement: Chequeo de tipos estricto
Ejecutar `mypy` desde `backend/` sin argumentos SHALL chequear en modo estricto, con Python 3.12 como versión objetivo, tanto el paquete `app` como los tests, y terminar sin errores.

#### Scenario: Chequeo de tipos limpio
- **WHEN** se ejecuta `mypy` en `backend/` con el entorno virtual activo
- **THEN** chequea `app` y `tests` en modo estricto y reporta cero errores

#### Scenario: Código sin anotaciones rechazado
- **WHEN** un módulo de `app` o de `tests` define una función sin anotaciones de tipos
- **THEN** `mypy` reporta un error para esa función

### Requirement: Artefactos locales fuera del control de versiones
El repositorio SHALL ignorar en git el entorno virtual y los cachés de Python, pytest y mypy, conservando las exclusiones existentes (`node_modules/` y `.env`).

#### Scenario: Artefactos generados no aparecen en git
- **WHEN** después de crear el venv y correr `pytest` y `mypy` se consulta `git status`
- **THEN** no aparecen `.venv/`, `__pycache__/`, `.pytest_cache/` ni `.mypy_cache/` como archivos sin seguimiento

### Requirement: Instrucciones de uso del backend
`backend/README.md` SHALL explicar en español cómo crear el entorno virtual con Python 3.13, instalar el proyecto con el grupo `dev` y correr `pytest` y `mypy`.

#### Scenario: Seguir el README desde cero
- **WHEN** una persona sigue los pasos del README en una máquina Windows con Python 3.13
- **THEN** obtiene un entorno donde `pytest` y `mypy` corren en verde
