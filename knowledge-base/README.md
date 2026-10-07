# turnos-odontologia — Base de Conocimiento

Base de conocimiento generada a partir de los documentos de Discovery (`docs/discovery/`) y de la decisión de stack confirmada por la autora. Describe un sistema web de gestión de turnos para consultorios odontológicos pequeños de Argentina, centrado en una agenda sin conflictos.

## Índice de Archivos

| Archivo | Contenido |
|---------|-----------|
| [01_vision_y_objetivos.md](01_vision_y_objetivos.md) | Propósito, objetivos por actor, alcance MVP, fuera de alcance, métricas |
| [02_descripcion_general.md](02_descripcion_general.md) | Stack TypeScript, arquitectura general, API REST, zona horaria |
| [03_actores_y_roles.md](03_actores_y_roles.md) | Actores, matriz RBAC, autenticación simulada, rutas públicas |
| [04_modelo_de_datos.md](04_modelo_de_datos.md) | Entidades SQLite, ERD, constraints, seed ficticio |
| [05_reglas_de_negocio.md](05_reglas_de_negocio.md) | Reglas RN-AG, RN-TU, RN-DI, RN-PA, RN-AC, RN-GL |
| [06_funcionalidades.md](06_funcionalidades.md) | Épicas, historias US-NNN y criterios de aceptación (escenarios de test) |
| [07_flujos_principales.md](07_flujos_principales.md) | Flujos de alta, reprogramación, estados, bloqueos, contrato de errores |
| [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md) | Patrones, estructura de monorepo, estrategia de tests, seguridad, env vars |
| [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md) | Decisiones DD-01..09 y supuestos SU-01..10 |
| [10_preguntas_abiertas.md](10_preguntas_abiertas.md) | Inconsistencias, preguntas Q-01..12, riesgos |

## Quick Start para Desarrolladores

1. Entender el dominio → [01](01_vision_y_objetivos.md), [03](03_actores_y_roles.md)
2. Entender los datos → [04](04_modelo_de_datos.md)
3. Entender las reglas → [05](05_reglas_de_negocio.md)
4. Entender la arquitectura → [02](02_descripcion_general.md), [08](08_arquitectura_propuesta.md)
5. Implementar → [07](07_flujos_principales.md), [06](06_funcionalidades.md)
6. Antes de codificar → [09](09_decisiones_y_supuestos.md) y [10](10_preguntas_abiertas.md)

## Resumen Ejecutivo

Sistema web para consultorios de 2 a 5 profesionales cuyo diferencial es rechazar, desde un dominio TypeScript puro y con mensajes explicativos, todo turno que se solape por profesional o por sillón, caiga fuera de horario o bloqueos, o esté en el pasado. Stack: TypeScript full-stack (dominio puro con Vitest y Strict TDD, API Fastify + SQLite, frontend React + Vite). El change evaluado en el ciclo OPSX del TP es C-02 `crear-turno-sin-solapamientos` (C-01 es su prerrequisito técnico): implementa solo el dominio de "crear un turno sin solapamientos por profesional y por sillón" (con duración por prestación, rechazo de duración no positiva y turnos consecutivos); horarios, bloqueos y el resto de las validaciones del turno van en C-03 a C-08 y la interfaz en C-22 a C-29 (el orden completo está en `CHANGES.md`). Plazos: hay un avance el 2026-10-08 sin contenido exigido definido y la entrega final es la semana siguiente (fecha a confirmar); trabajo individual, solo datos ficticios y sin credenciales en el repo. Los defaults del MVP para las preguntas abiertas figuran como **Suposición:** en 09 y 10.
