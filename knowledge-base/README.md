# turnos-odontologia — Base de Conocimiento

Base de conocimiento generada a partir de los documentos de Discovery (`docs/discovery/`) y actualizada con el stack fijado por la cátedra el 2026-10-08 (DD-01). Describe un sistema web de gestión de turnos para consultorios odontológicos pequeños de Argentina, centrado en una agenda sin conflictos.

## Índice de Archivos

| Archivo | Contenido |
|---------|-----------|
| [01_vision_y_objetivos.md](01_vision_y_objetivos.md) | Propósito, objetivos por actor, alcance MVP, fuera de alcance, métricas |
| [02_descripcion_general.md](02_descripcion_general.md) | Stack de la cátedra (FastAPI, PostgreSQL, Redis, Docker; React + TS + Vite), arquitectura general, API REST, zona horaria |
| [03_actores_y_roles.md](03_actores_y_roles.md) | Actores, matriz RBAC, autenticación JWT, rutas públicas |
| [04_modelo_de_datos.md](04_modelo_de_datos.md) | Entidades PostgreSQL (SQLAlchemy), ERD, constraints, seed ficticio |
| [05_reglas_de_negocio.md](05_reglas_de_negocio.md) | Reglas RN-AG, RN-TU, RN-DI, RN-PA, RN-AC, RN-GL |
| [06_funcionalidades.md](06_funcionalidades.md) | Épicas, historias US-NNN y criterios de aceptación (escenarios de test) |
| [07_flujos_principales.md](07_flujos_principales.md) | Flujos de alta, reprogramación, estados, bloqueos, contrato de errores |
| [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md) | Patrones, estructura `backend/` + `frontend/`, estrategia de tests, seguridad, Docker Compose, Redis, env vars |
| [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md) | Decisiones DD-01..11, supuestos SU-01..11 y decisiones reemplazadas |
| [10_preguntas_abiertas.md](10_preguntas_abiertas.md) | Inconsistencias, preguntas Q-01..14, riesgos |

## Quick Start para Desarrolladores

1. Entender el dominio → [01](01_vision_y_objetivos.md), [03](03_actores_y_roles.md)
2. Entender los datos → [04](04_modelo_de_datos.md)
3. Entender las reglas → [05](05_reglas_de_negocio.md)
4. Entender la arquitectura → [02](02_descripcion_general.md), [08](08_arquitectura_propuesta.md)
5. Implementar → [07](07_flujos_principales.md), [06](06_funcionalidades.md)
6. Antes de codificar → [09](09_decisiones_y_supuestos.md) y [10](10_preguntas_abiertas.md)

## Resumen Ejecutivo

Sistema web para consultorios de 2 a 5 profesionales cuyo diferencial es rechazar, desde un dominio Python puro y con mensajes explicativos, todo turno que se solape por profesional o por sillón, caiga fuera de horario o bloqueos, o esté en el pasado. Stack fijado por la cátedra (2026-10-08): backend Python + FastAPI con JWT, SQLAlchemy y PostgreSQL, Redis para lo asincrónico (sin uso en el MVP), Docker Compose; dominio puro dentro del backend con pytest y Strict TDD; frontend React + TypeScript + Vite. El change evaluado en el ciclo OPSX del TP es C-02 `crear-turno-sin-solapamientos` (C-01 es su prerrequisito técnico): implementa solo el dominio de "crear un turno sin solapamientos por profesional y por sillón" (con duración por prestación, rechazo de duración no positiva y turnos consecutivos); horarios, bloqueos y el resto de las validaciones del turno van en C-03 a C-08 y la interfaz en C-22 a C-29 (el orden completo está en `CHANGES.md`). Plazos: el avance del 2026-10-08 solo pide el Discovery (ya hecho) y la entrega final es el jueves 2026-10-15; trabajo individual, solo datos ficticios y sin credenciales en el repo. Los defaults del MVP para las preguntas abiertas figuran como **Suposición:** en 09 y 10.
