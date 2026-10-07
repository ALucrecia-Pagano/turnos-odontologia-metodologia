# Checklist de Discovery — Sistema de turnos para consultorios odontológicos

**Fecha:** 2026-10-03
**Estado:** confirmado por la autora (gate final de Discovery).
**Informe de mercado asociado:** [informe-discovery.md](informe-discovery.md)
**Fichas por sistema:** [sources/](sources/)

> Las decisiones de producto de este checklist son de la autora. Donde el análisis de mercado sugirió algo distinto, se indica explícitamente.

---

## 1. Problema que resuelve

Los consultorios odontológicos pequeños de Argentina gestionan la agenda en papel, planillas o WhatsApp. Ese método produce solapamientos de profesionales y de sillones y vuelve desordenada la operación diaria. El sistema garantiza una agenda sin conflictos.

- **Dolor principal elegido:** agenda desordenada (solapamientos, múltiples profesionales y sillones).
- **Dolores secundarios, no prioritarios en el MVP:** ausentismo de pacientes y reserva fuera de horario.

## 2. Usuarios y roles

**Segmento:** consultorio pequeño, con 2 a 5 profesionales, varios sillones y secretaria o recepción.

| Rol | Verbo principal | Alcance |
|---|---|---|
| Odontólogo | Consulta su agenda; gestiona sus horarios y bloqueos | MVP |
| Secretaria / recepción | Da, mueve y cancela turnos de todos los profesionales | MVP |
| Administrador / dueño | Configura consultorio, profesionales, sillones y prestaciones | MVP |
| Paciente (autogestión) | Reserva, confirma, cancela o reprograma por su cuenta | Posterior al MVP |

## 3. Casos de uso principales

1. Como **secretaria**, quiero dar un turno eligiendo paciente, profesional, sillón y prestación, para que el sistema lo rechace si se superpone o cae fuera de horario.
2. Como **secretaria**, quiero reprogramar o cancelar un turno, para mantener la agenda al día.
3. Como **odontólogo**, quiero cargar mi horario de atención y mis bloqueos, para que no me asignen turnos cuando no atiendo.
4. Como **administrador**, quiero configurar profesionales, sillones y prestaciones con su duración, para que cada turno ocupe el tiempo correcto.
5. Como **recepción u odontólogo**, quiero ver la agenda diaria y semanal por profesional y por sillón, y marcar cada turno como confirmado, atendido o ausente.

## 4. Competidores y soluciones existentes

Se relevaron 26 sistemas de Argentina, Latinoamérica y referentes internacionales, solo con fuentes públicas verificables y sin contactar proveedores. El detalle completo está en [informe-discovery.md](informe-discovery.md), secciones A a D.

Los cinco primeros por evidencia pública ponderada (matriz B) son:

| Puesto | Sistema | Total |
|---|---|---|
| 1 | Odonthia | 3,25 |
| 2 | DentalCore | 3,15 |
| 3 | Dentalink | 3,00 |
| 4 | Open Dental | 2,95 |
| 5 | Bilog | 2,80 |

> El puntaje mide la evidencia pública disponible, no la capacidad real del producto. La matriz se verifica con [verificar_matriz.py](verificar_matriz.py).

## 5. Funcionalidades necesarias (MVP)

| Funcionalidad | Change previsto |
|---|---|
| Crear un turno sin solapamientos por profesional ni por sillón, con mensajes de conflicto claros que indiquen qué turno o bloqueo choca | **Primer change** (solo lógica de dominio) |
| Horario de atención por profesional y bloqueos (vacaciones, feriados, ausencias) | Posterior |
| Catálogo de prestaciones con duración por defecto, editable al dar el turno | Posterior |
| Ciclo de vida del turno: cancelar y reprogramar, con estados reservado, confirmado, atendido, ausente y cancelado | Posterior |
| Historial de cambios de estado del turno (quién cambió qué y cuándo) | Change del ciclo de vida del turno |
| Datos mínimos del paciente: nombre, DNI, teléfono, obra social como texto; siempre ficticios y sin información clínica | Posterior |
| Vista diaria y semanal por profesional y por sillón, incluida una vista de recepción por sillón | Change de interfaz web |

**Diferenciadores incluidos en el MVP:**
- Mensajes de conflicto claros.
- Vista de recepción por sillón.

**Primer change:** solo crear un turno sin solapamientos. La interfaz se construye en un change posterior, sobre la lógica ya probada.

## 6. Funcionalidades opcionales (backlog posterior al MVP)

- Búsqueda del primer hueco disponible que cumpla profesional, sillón y duración. Fue sugerida por el análisis y quedó fuera del MVP por decisión de la autora.
- Sobreturnos con marca explícita y límite por franja o profesional.
- Regla que impide que un paciente tenga dos turnos simultáneos.
- Confirmación o cancelación mediante enlace de WhatsApp, y luego por la API oficial.
- Reserva online del paciente con aprobación del consultorio.
- Lista de espera para ofrecer turnos liberados.
- Seña al reservar, con integración de Mercado Pago.
- Facturación con ARCA y gestión de obras sociales y prepagas.
- Ficha clínica y odontograma.
- Múltiples sedes, reportes y exportación de datos.

## 7. Reglas de negocio

**Vigentes en el MVP:**
1. Un profesional no puede tener dos turnos superpuestos.
2. Un sillón o box no puede asignarse a dos turnos superpuestos.
3. Los sobreturnos están prohibidos: todo solapamiento se rechaza.
4. El turno debe caer completo dentro del horario de atención del profesional y fuera de sus bloqueos.
5. No se puede dar ni reprogramar un turno en una fecha u hora pasada.
6. La duración del turno es variable: cada prestación define una duración por defecto.

**Diferidas a changes posteriores:**
- Un paciente no puede tener dos turnos simultáneos.
- Sobreturnos con marca explícita y límite.

## 8. Integraciones

**Ninguna en el MVP.** WhatsApp, Google Calendar, Mercado Pago y ARCA quedan documentadas como etapas posteriores (ver punto 6).

## 9. Restricciones

| Restricción | Origen |
|---|---|
| Entrega el jueves 8 de octubre de 2026 | Cátedra |
| Trabajo individual | Cátedra |
| Tests automatizados que cubran cada escenario del spec | Cátedra |
| Solo datos ficticios; nunca datos reales de pacientes | Cátedra |
| Sin claves ni credenciales en el repositorio | Cátedra |
| Primer change chico y terminable, centrado en la lógica de dominio de la agenda; la interfaz va en un change posterior | Cátedra |
| Stack libre, definido por la autora | Decisión propia |
| Interfaz gráfica web con un frontend cuidado | Decisión propia |
| Sin contactar proveedores ni crear cuentas para evaluar productos | Consigna de investigación |

## 10. Riesgos

**Señalados por la autora:**
1. **Plazo de 5 días:** no llegar a terminar la lógica de dominio y la interfaz con calidad para el 8/10.
2. **Reglas de agenda incompletas:** que aparezcan casos borde de solapamiento, horarios o zona horaria no previstos en el spec.
3. **Calidad del frontend:** que la interfaz no quede cuidada por llegar al final del plazo.

**Supuestos sin verificar detectados en el análisis de mercado:**
4. Que la competencia "no tenga" prevención de solapamientos significa solo que no está evidenciada públicamente; no prueba que no exista.
5. El tamaño del segmento (2 a 5 profesionales, con secretaria y varios sillones) no tiene datos de mercado que lo respalden.
6. Sin recordatorios por WhatsApp, el MVP puede parecer incompleto frente a herramientas gratuitas como Odonthia, SimpleTurno o Turnito.
7. Un producto real exigiría cumplir la Ley 25.326 (datos personales) y la Ley 26.529 (derechos del paciente). En el mercado es habitual alojar los datos en el exterior.
8. La evidencia de mercado proviene de resúmenes de páginas. El sitio argentino de Doctoralia no fue accesible, y las cifras de adopción son declaraciones de los proveedores. El 2026-10-06 la autora verificó manualmente cinco fuentes (ver "Verificación de fuentes" en el informe); el resto no se verificó a mano.
9. **El MVP puede resultar demasiado estricto en el uso real.** El competidor mejor documentado (Odonthia) eligió avisar en lugar de bloquear: en su agenda interna, superar la capacidad o agendar fuera de horario genera un aviso que se puede forzar ("una urgencia un domingo es legítima"). El MVP, en cambio, prohíbe los sobreturnos y rechaza los turnos fuera de horario.

## 11. Preguntas abiertas

Ninguna bloquea el cierre de Discovery. Se resuelven en la propuesta del change correspondiente.

1. ¿Hace falta una anticipación mínima para cancelar un turno, por ejemplo 24 horas?
2. ¿Un turno puede marcarse "ausente" antes de su hora de inicio?
3. ¿Qué transiciones de estado son válidas? Por ejemplo, si se puede reprogramar un turno atendido o reactivar uno cancelado.
4. ¿Qué pasa con los turnos existentes cuando se crea un bloqueo que los pisa?
   *Referencia de mercado, no decidida:* en Odonthia, "bloquear un día no cancela los turnos que ya tenías agendados ahí: esos los seguís viendo y los reprogramás vos" (documentación de agenda, verificada manualmente el 2026-10-06).
5. ¿Algunas prestaciones exigen un sillón específico?
6. ¿Qué zona horaria y qué granularidad de horario se usan? Se propone America/Argentina/Buenos_Aires.
7. ¿Con qué stack se implementa? Lo define la autora.
