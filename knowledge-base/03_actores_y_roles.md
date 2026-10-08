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

**Suposición:** el MVP **no implementa autenticación real**. El rol se simula con una sesión de desarrollo (selector de rol en la UI y cabecera `X-Role` / `X-User-Id` en la API, solo con `NODE_ENV != production`). Motivo: plazo acotado (entrega final el jueves 2026-10-15), restricción de no guardar credenciales en el repo y foco del MVP en la lógica de agenda. Autenticación real (hash de contraseñas, sesión/JWT) queda para un change posterior y sería dominio de gobernanza **CRITICAL** (requiere aprobación humana explícita antes de escribir código). Ver SU-06.

## Rutas públicas

| Ruta | Descripción |
|------|-------------|
| `GET /api/health` | Estado del servicio |
| (Posterior al MVP) reserva online del paciente | No existe en el MVP |

En el MVP todo el resto de la API requiere identificar un rol (sesión simulada).
