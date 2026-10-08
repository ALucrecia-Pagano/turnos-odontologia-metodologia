# Actores y Roles

## Actores del sistema

| Actor | Descripción | Cómo interactúa | Alcance |
|-------|-------------|-----------------|---------|
| Odontólogo | Profesional que atiende; hasta 5 por consultorio | Consulta su agenda; carga su horario de atención y sus bloqueos; marca estados de sus turnos | MVP |
| Secretaria / recepción | Persona que administra la agenda de todos los profesionales | Da, mueve y cancela turnos; ve la agenda por profesional y por sillón; marca confirmado/ausente | MVP |
| Administrador / dueño | Responsable del consultorio | Configura profesionales, sillones y prestaciones (con duración); gestiona usuarios y horarios | MVP |
| Paciente | Persona atendida | Autogestión de turnos (reservar, confirmar, cancelar, reprogramar) | **Posterior al MVP** (no hay usuario paciente en el MVP) |
| Sistema | Motor de agenda | Valida reglas RN-AG, registra historial | — |

En el MVP el paciente es una **entidad de datos** (datos mínimos ficticios), no un usuario con acceso.

## RBAC — Matriz de permisos

Leyenda: C crear · R leer · U actualizar · D borrar · `—` sin acceso · `propio` solo sobre sus propios registros.

| Recurso | Odontólogo | Recepción | Administrador |
|---------|------------|-----------|---------------|
| Turnos (dar) | — (**Suposición:** no da turnos) | C | C |
| Turnos (leer agenda) | R (propios; **Suposición:** puede ver la agenda completa en solo lectura) | R (todos) | R (todos) |
| Turnos (reprogramar / cancelar) | — | U (todos) | U (todos) |
| Turnos (cambiar estado: confirmado, atendido, ausente) | U (propios) | U (todos) | U (todos) |
| Historial de turno | R (propios) | R (todos) | R (todos) |
| Horario de atención | CRU propio | R | CRUD |
| Bloqueos | CRUD propio | R | CRUD |
| Profesionales | R | R | CRUD |
| Sillones | R | R | CRUD |
| Prestaciones (catálogo y duración) | R | R | CRUD |
| Pacientes (datos mínimos ficticios) | R | CRU | CRU |
| Usuarios y roles | — | — | CRUD |

**Suposición:** el Odontólogo no da turnos nuevos en el MVP (el discovery asigna ese verbo a recepción); si se requiere, se habilita sin cambiar el dominio. Ver [10_preguntas_abiertas.md](10_preguntas_abiertas.md).

### Autenticación en el MVP

**Decisión de la cátedra (2026-10-08):** la autenticación es con **JWT** y reemplaza al rol simulado que proponía la versión anterior de esta KB (SU-06 v1). Se mantienen los tres roles (`odontologo`, `recepcion`, `administrador`) y la matriz RBAC de arriba.

- `POST /api/auth/login` recibe usuario y contraseña y devuelve un token de acceso con `sub` (id de usuario), `role` y `exp`, firmado con `JWT_SECRET`.
- Las rutas protegidas exigen `Authorization: Bearer <token>`; la API toma el rol y el usuario del token, no de cabeceras enviadas por el cliente.
- Las contraseñas se guardan solo como hash. Los usuarios del seed son ficticios y su contraseña sale de `.env` (`SEED_USER_PASSWORD`); ninguna credencial queda en el repo.
- **Suposición:** sin refresh tokens ni revocación en el MVP (SU-06).

Es un change posterior a C-02 (API base, C-16; login en la web, C-22) y de gobernanza **CRITICAL**: requiere aprobación humana explícita antes de escribir código. Ver DD-11.

## Rutas públicas

| Ruta | Descripción |
|------|-------------|
| `GET /api/health` | Estado del servicio |
| `POST /api/auth/login` | Inicio de sesión; devuelve el JWT |
| (Posterior al MVP) reserva online del paciente | No existe en el MVP |

En el MVP todo el resto de la API requiere un JWT válido: sin token o con token inválido o vencido → `401`; rol sin permiso → `403`.
