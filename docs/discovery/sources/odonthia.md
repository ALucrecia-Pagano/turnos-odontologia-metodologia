# Odonthia

| Campo | Valor |
|---|---|
| Producto | Odonthia [F1] |
| Empresa proveedora | Genera Impacto; fundador Manuel Sabio [F1] |
| País de origen | Argentina (sitio oficial) [F1] |
| URL oficial | https://odonthia.com/ |
| Segmento objetivo | Odontólogo independiente y consultorio; admite equipo y sedes [F1][F5] |
| Modalidad | SaaS en la nube (Supabase sobre AWS São Paulo, Comprobado en seguridad) [F4] |
| Presencia en Argentina | Sí; precios en pesos argentinos, plan para Argentina [F2] |

## 1. Gestión de agenda
- Vistas día, semana y mes; botón "Compacto" para móvil (Comprobado, documentación) [F5]
- Múltiples profesionales: una columna por profesional, con color propio; no permite que un profesional esté en dos lugares a la vez (Comprobado) [F5]
- Múltiples sillones: se configura por sede la cantidad de pacientes simultáneos; con valor 1, impide solapamientos entre profesionales (Comprobado) [F5]
- Duración variable: sugerida desde la lista de precios y ajustable por turno (Comprobado) [F5]
- Bloqueos: botón "Bloquear días", hasta 90 días consecutivos, no cancela turnos existentes (Comprobado) [F5]
- Sobreturnos: alerta al exceder la capacidad y permite forzar (Comprobado) [F5]
- Sala de espera con lista por orden de llegada; se marca en rojo tras 20 minutos (Comprobado) [F5]

## 2. Turnos digitales
- Reserva online del paciente en una página propia del consultorio: elige servicio, profesional, fecha y hora; llega como pendiente y se confirma desde la agenda; hasta 30 días de anticipación; no ofrece turnos dentro de las próximas 2 horas (Comprobado, documentación) [F6]
- Enlace/QR y texto para redes sociales; carteles imprimibles; posible aparición en Google si hay dirección y teléfono (Comprobado) [F6]
- Confirmación o cancelación por el paciente desde el enlace de WhatsApp, con actualización automática del estado (Comprobado) [F5]
- Sincronización con Google, Apple y Outlook Calendar (Declarado en funcionalidades) [F3]; importa compromisos de Google Calendar como tiempo bloqueado (Comprobado) [F5]
- Chatbot, lista de espera (distinta de la sala de espera): No evidenciado

## 3. Automatización
- Recordatorio por WhatsApp: el mensaje incluye paciente, fecha, hora, profesional, servicio, sede y enlace de confirmación; en la documentación el personal abre el chat con el texto precargado y lo envía manualmente (Comprobado) [F5]
- Planes pagos: "WhatsApp automático" incluido (Declarado) [F2]
- Seguimiento de ausentes, recuperación, controles periódicos, campañas: No evidenciado

## 4. Gestión odontológica
- Odontograma digital con notación FDI (incluye dentición temporal), ficha clínica con alergias y medicación (Declarado) [F3][F1]
- Periodontograma de seis sitios por diente con comparación fechada (Declarado) [F3]; módulo de ortodoncia (Declarado) [F3]
- Presupuestos y planes con firma digital móvil; lista de precios con duración (Declarado) [F3]
- Historia clínica digital conforme a Ley 26.529 y firma electrónica según Ley 25.506; consentimientos informados (Declarado en home) [F1]; firmas remotas con sello de tiempo, IP, dispositivo y hash SHA-256 (Comprobado) [F4]
- IA (de pago): notas clínicas por voz, análisis de radiografías (2 a 5 créditos) (Declarado) [F2][F3]
- Imágenes/radiografías como archivos: se recuperan por solicitud (Comprobado) [F4]

## 5. Administración
- Seña opcional al agendar (efectivo, transferencia o tarjeta), registrada como asiento en la cuenta del paciente y reportes (Comprobado) [F5]
- Caja y reportes de ingresos, egresos y saldos (Declarado) [F3]
- Mercado Pago, facturación electrónica ARCA, liquidaciones a obras sociales: No evidenciado (una comparación publicada por el propio proveedor indica que no gestiona facturación a obras sociales; no se usa como fuente) 
- Información de obra social del paciente en su ficha (Declarado) [F1]

## 6. Integraciones
- WhatsApp Business (Declarado) [F3]; Google/Apple/Outlook Calendar (Declarado) [F3][F5]
- Importación CSV de hasta 1.000 pacientes por lote y asistencia de migración (Declarado) [F1]
- API pública, Mercado Pago, ARCA, radiología: No evidenciado

## 7. Operación
- Sedes con horarios y sillones propios; profesional con horario por sede (Comprobado) [F5]
- Roles: Titulares, Profesionales y Administrativos (Comprobado) [F4]
- Exportación completa de pacientes, historias, turnos y cuentas en Excel desde Configuración; archivos (radiografías, fotos) por solicitud (Comprobado) [F4]
- Documentación pública (/docs) y soporte prioritario en plan Max (Declarado) [F2][F5]
- Auditoría general de acciones: No evidenciado (solo registro de firma remota) [F4]

## 8. Seguridad y cumplimiento
- Datos en PostgreSQL (Supabase) sobre AWS São Paulo, Brasil; HTTPS/TLS y AES-256 en reposo (Comprobado) [F4]
- Respaldos diarios automáticos de la infraestructura (Comprobado) [F4]
- Aislamiento por consultorio; contraseñas con bcrypt; retención mínima de historias de 10 años (Ley 26.529) (Comprobado) [F4]
- Baja: copia completa, 30 días de gracia y eliminación definitiva (Comprobado) [F4]
- Ley 25.326: No evidenciado (la página de seguridad no la menciona) [F4]; Ley 27.706: No evidenciado

## 9. Modelo comercial
- Odonthia Gratis: sin límite de pacientes; ficha clínica, odontograma, agenda, pacientes y documentos; 2 consultas de IA; sin tarjeta (Comprobado, página de planes) [F2]
- Odonthia IA: Argentina ARS 20.900/mes o ARS 209.000/año; resto de LatAm USD 26/mes o USD 260/año; 60 créditos IA; WhatsApp automático y mensajería interna [F2]
- Odonthia Max: Argentina ARS 46.900/mes o ARS 469.000/año; LatAm USD 44/mes o USD 440/año; 200 créditos; soporte prioritario [F2]
- Paquetes de créditos únicos: 20 créditos ARS 8.400 / USD 9; 100 créditos ARS 36.900 / USD 35 [F2]
- Política de reembolsos enlazada (no inspeccionada) [F1]

## 10. Fortalezas, limitaciones y diferenciales evidentes
**Fortalezas:** plan gratuito sin límite de pacientes con agenda y odontograma; documentación pública detallada y verificable de agenda, reserva online, sedes y roles; precios en ARS y USD publicados; exportación Excel y respaldos diarios.
**Limitaciones:** el recordatorio por WhatsApp documentado es de envío manual en el plan base; sin evidencia de facturación ARCA, obras sociales ni Mercado Pago; datos alojados en Brasil; Ley 25.326 no citada; funciones de IA con costo por créditos.
**Diferenciales:** modelo gratuito de base; reserva online con aprobación y control de capacidad por sede; firma digital con trazabilidad (hash SHA-256).

## 11. Evidencia de adopción
- "2.714 consultorios registrados usando Odonthia" (Declarado) [F1]
- Casos de éxito y reseñas verificables (Capterra, Google Play, App Store): no halladas

## Evidencia para puntuación (no puntuar, solo resumir en 1 línea por criterio)
- Turnos y automatización: agenda multi-profesional, bloqueos, sobreturnos y reserva online comprobados; recordatorio WhatsApp manual en base, automático en plan pago (declarado).
- Clínica odontológica: odontograma, periodontograma y presupuestos declarados; firma digital comprobada.
- Integraciones locales y WhatsApp: WhatsApp y calendarios declarados; sin ARCA ni Mercado Pago.
- Administración, cobros, facturación: señas comprobadas; caja declarada; sin facturación fiscal evidenciada.
- Experiencia del paciente: reserva online personalizable, QR y confirmación por enlace comprobados.
- Seguridad, exportación, trazabilidad: cifrado, respaldos diarios, roles y exportación Excel comprobados; Ley 25.326 no citada.
- Precio y facilidad de adopción: plan gratuito, sin tarjeta, importación CSV; planes de pago publicados.

## Fuentes
| # | Tipo (oficial/precios/ayuda/video/tienda/reseñas) | URL | Fecha de consulta |
|---|---|---|---|
| F1 | oficial | https://odonthia.com/ | 2026-10-03 |
| F2 | precios | https://odonthia.com/planes | 2026-10-03 |
| F3 | oficial (funcionalidades) | https://odonthia.com/funcionalidades | 2026-10-03 |
| F4 | oficial (seguridad) | https://odonthia.com/seguridad | 2026-10-03 |
| F5 | ayuda (documentación: agenda y turnos) | https://odonthia.com/docs/agenda-y-turnos.md | 2026-10-03 |
| F6 | ayuda (documentación: reserva online) | https://odonthia.com/docs/reserva-online.md | 2026-10-03 |
| F7 | ayuda (índice de documentación) | https://odonthia.com/docs | 2026-10-03 |
