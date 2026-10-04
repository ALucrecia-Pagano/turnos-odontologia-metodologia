# DentalCore

| Campo | Valor |
|---|---|
| Producto | DentalCore (Sistema de Información en Salud con soporte a la decisión clínica, CDSS) [F1] |
| Empresa proveedora | Alfredo Di Tullio (odontólogo, M.N. 40.973; CUIT 20-40568642-3), responsable del tratamiento; CTO Ignacio Naveilhan [F1][F5][F6] |
| País de origen | Argentina, La Plata (sitio oficial) [F1][F5] |
| URL oficial | https://dentalcore.app/ |
| Segmento objetivo | Consultorios y clínicas multiprofesional/multisede (Declarado) [F1] |
| Modalidad | SaaS en la nube (app.dentalcore.app) (Declarado) [F1] |
| Presencia en Argentina | Planes de salud argentinos precargados, ARCA, Mercado Pago (Declarado) [F1] |

## 1. Gestión de agenda
- Agenda visual multi-profesional con arrastrar y soltar (Declarado) [F1]
- Sala de espera virtual (Declarado) [F1]
- Múltiples sillones/boxes, duración variable, bloqueos, sobreturnos, prevención de solapamientos: No evidenciado

## 2. Turnos digitales
- Reserva y cancelación online desde portal del paciente (Declarado) [F1]
- Bot de WhatsApp con 9 automatizaciones (confirmaciones, relleno de huecos, recalls) (Declarado) [F1]
- Chatbot de IA en el portal del paciente (Declarado) [F1]
- Teleodontología por video (Declarado) [F1]
- Lista de espera, reprogramación explícita: No evidenciado (la sala de espera virtual no equivale a lista de espera)

## 3. Automatización
- Recordatorios automáticos y confirmaciones; relleno de huecos y recalls por el bot de WhatsApp (Declarado) [F1]
- Seguimiento de ausentes y campañas: No evidenciado

## 4. Gestión odontológica
- Odontograma y periodontograma digitales (Declarado) [F1]
- Historia clínica con control por voz y asistente "Sani"; 17 motores de decisión clínica y 12+ módulos de especialidad (Declarado; el "Acerca de" indica 15+ módulos) [F1][F5]
- Presupuestos versionados (Declarado) [F1]
- Consentimientos digitales firmados, comparación de fotos antes/después (Declarado) [F1]
- Imágenes/radiografías: fotos comparativas declaradas; radiografías específicas No evidenciado

## 5. Administración
- Facturación electrónica ARCA (Declarado) [F1]
- 20+ planes de salud precargados (PAMI, OSDE, IOMA, Swiss Medical, Galeno, Sancor) (Declarado) [F1]
- Mercado Pago con QR (Declarado) [F1]; caja diaria; panel "Oro perdido" de cobros pendientes (Declarado) [F1]
- Liquidaciones a obras sociales: No evidenciado
- Inventario con escaneo de facturas, órdenes de laboratorio, chat interno y tareas (Declarado) [F1]

## 6. Integraciones
- WhatsApp, ARCA, Mercado Pago, HL7 FHIR (Declarado) [F1]; cobro de la suscripción vía Paddle o Stripe (Comprobado en términos) [F4]
- Google Calendar, API pública, radiología, firma digital certificada: No evidenciado

## 7. Operación
- Multi-sucursal (Declarado) [F1]
- Soporte directo del fundador, respuesta en menos de 24 horas (Declarado) [F1][F3]; asistencia de migración y DentalCore Academy (Declarado) [F1]
- Exportación: ventana de 30 días tras la baja para descargar datos (Comprobado en términos) [F4]
- Roles y permisos: No evidenciado en detalle
- Rastro de auditoría de accesos (Declarado, citado como Ley 26.529) [F1]

## 8. Seguridad y cumplimiento
- Política de privacidad bajo Ley 25.326 y supervisión de la AAIP; el dentista es responsable de los datos y DentalCore encargado del tratamiento (Comprobado) [F6]
- Cifrado en tránsito (TLS) y en reposo, control de acceso por roles, monitoreo de incidentes; datos en Supabase/AWS, posiblemente fuera de Argentina con transferencia internacional consentida (Comprobado) [F6]
- Respaldos automáticos continuos declarados en privacidad [F6]; los términos no mencionan servicio de respaldo automático (Comprobado) [F4]
- Declarados: ISO/IEC 27001 (como controles, no certificación), AES-256-GCM para claves fiscales, scrypt, base aislada por clínica, auditoría de acceso (Ley 26.529) (Declarado) [F1]
- Sin garantía de disponibilidad del 100% (Comprobado) [F4]
- La FAQ de seguridad y respaldos aparece sin respuestas visibles (No evidenciado) [F3]
- Ley 27.706: No evidenciado

## 9. Modelo comercial
- Plan único: USD 50/mes con 2 usuarios incluidos; usuario adicional USD 10/mes; pacientes ilimitados; 50 GB incluidos (Comprobado, página de precios) [F2]
- Todo incluido, sin cargos separados por WhatsApp, IA ni módulos (Comprobado en precios) [F2]
- Cobro en moneda local al tipo de cambio del día; tarjeta, Mercado Pago, PayPal o transferencia; renovación mensual automática; ajustes con aviso de 30 días [F2][F4]
- Garantía de 14 días con devolución del dinero (el home la llama prueba de 14 días) [F1][F2]
- Plan gratuito: No evidenciado

## 10. Fortalezas, limitaciones y diferenciales evidentes
**Fortalezas:** precio único público y transparente; paquete amplio de funciones; términos y privacidad detallados con referencia a la Ley 25.326 y a la AAIP; portal del paciente con reserva online declarado.
**Limitaciones:** producto nuevo ("a punto de lanzar" según su página de equipo); la mayoría de las funciones son declaradas; precio en USD sujeto a cambio; datos fuera de Argentina; FAQ de seguridad sin respuestas visibles; sin cifras de clientes.
**Diferenciales:** CDSS basado en reglas (no IA generativa para decisión clínica, Declarado); creado por un odontólogo en ejercicio; asistente por voz.

## 11. Evidencia de adopción
- Clientes publicados: No evidenciado; la página "Acerca de" indica que está "por lanzar" con adoptantes tempranos [F5]
- Reseñas verificables (Capterra, tiendas): no halladas
- Un artículo externo de comparación menciona lanzamiento comercial en 2025 sin fuente verificable; no se usa como evidencia

## Evidencia para puntuación (no puntuar, solo resumir en 1 línea por criterio)
- Turnos y automatización: agenda multi-doctor y bot WhatsApp de 9 automatizaciones, solo declarados.
- Clínica odontológica: odontograma, periodontograma, CDSS y especialidades declarados; sin demostración pública.
- Integraciones locales y WhatsApp: ARCA, Mercado Pago, WhatsApp y planes argentinos declarados.
- Administración, cobros, facturación: facturación, caja y presupuestos declarados; sin liquidaciones a obras sociales.
- Experiencia del paciente: portal con reserva, consentimientos y teleodontología declarados.
- Seguridad, exportación, trazabilidad: privacidad con Ley 25.326 y AAIP comprobada; exportación 30 días tras la baja; auditoría declarada.
- Precio y facilidad de adopción: USD 50/mes publicado, garantía de 14 días, sin permanencia.

## Fuentes
| # | Tipo (oficial/precios/ayuda/video/tienda/reseñas) | URL | Fecha de consulta |
|---|---|---|---|
| F1 | oficial | https://dentalcore.app/ | 2026-10-03 |
| F2 | precios | https://dentalcore.app/pricing | 2026-10-03 |
| F3 | ayuda (FAQ, respuestas no visibles) | https://dentalcore.app/faq | 2026-10-03 |
| F4 | oficial (términos) | https://dentalcore.app/terms | 2026-10-03 |
| F5 | oficial (acerca de) | https://dentalcore.app/about | 2026-10-03 |
| F6 | oficial (privacidad) | https://dentalcore.app/privacy | 2026-10-03 |
