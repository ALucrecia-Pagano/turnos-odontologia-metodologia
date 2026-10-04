# Informe de mercado: software de gestión de turnos y agenda para consultorios odontológicos en Argentina

## Resumen ejecutivo

**Qué se investigó.** Se relevaron 26 sistemas de gestión de turnos y agenda aptos para consultorios odontológicos: 16 de origen argentino o con presencia comercial en Argentina, 7 latinoamericanos o regionales sin presencia argentina comprobada y 3 referentes internacionales. Se usaron exclusivamente fuentes públicas (sitios oficiales, precios, centros de ayuda, manuales, términos, tiendas y plataformas de reseñas), consultadas el 2026-10-03, sin contactar proveedores ni crear cuentas. Cada afirmación se clasificó como **comprobada** (visible en documentación o ayuda) o **declarada** (solo afirmación comercial); lo que no tiene respaldo público figura como "No evidenciado".

**Hallazgos principales.**
1. **La evidencia pública es escasa.** El mejor puntaje ponderado es 3,50 sobre 5 (Odonthia), seguido por DentalCore (3,15), Dentalink (3,00), Open Dental (2,95) y Bilog (2,80). Los puntajes miden evidencia pública, no capacidad real.
2. **Los recordatorios por WhatsApp son el estándar declarado del mercado,** pero solo Dentalink y Odonthia los tienen comprobados en documentación, y ningún sistema evidencia el uso de la API oficial de WhatsApp Business.
3. **La prevención de solapamientos casi no está demostrada.** Solo Odonthia la comprueba en forma completa y Open Dental en forma parcial; la agenda por sillón o box solo está comprobada en Odonthia, Open Dental y DentalBox.
4. **El cumplimiento normativo argentino está poco evidenciado.** La Ley 25.326 está comprobada en cuatro sistemas, la Ley 26.529 solo en uno y ninguno evidencia la Ley 27.706; solo OdontoSoft Millennium tiene auditoría comprobada.
5. **Los precios son opacos en el segmento local:** Bilog, ClinIA, Geblix, OdontoGRAMA y OdonticLabs no publican precios, OdontoApp solo tiene una cifra no verificada y DentalTec publica únicamente el costo de la mensajería; varios cotizan en dólares y las integraciones locales (ARCA, Mercado Pago, obras sociales) son solo declaradas.

**MVP recomendado.** Un sistema web para consultorios pequeños (2 a 5 profesionales, varios sillones, con recepción) cuyo núcleo sea una **agenda sin conflictos**, el vacío más claro del mercado:
- **Imprescindibles:** prevención de solapamientos por profesional y por sillón validada en el dominio; turnos dentro del horario y fuera de bloqueos, nunca en el pasado; duración variable por prestación; ciclo de vida del turno con cinco estados e historial de transiciones; tres roles (odontólogo, recepción, administrador); datos mínimos y ficticios del paciente; vistas diaria y semanal.
- **Diferenciadores:** mensajes de rechazo explicativos ante cada conflicto y vista de recepción por sillón.
- **Para etapas posteriores:** búsqueda del primer hueco disponible, WhatsApp, reserva online del paciente, lista de espera, sobreturnos controlados, cobros e integraciones locales, historia clínica y multisede.

El primer change se limita a **crear un turno sin solapamientos por profesional y por sillón**; la interfaz se construye después, sobre esa lógica ya probada.

---

## Introducción

**Objetivo.** Caracterizar la oferta de software de gestión de turnos y agenda odontológica disponible para el mercado argentino, evaluar comparativamente su evidencia pública y derivar recomendaciones para el diseño del producto en desarrollo: un sistema web de gestión de turnos y agenda para consultorios odontológicos pequeños de Argentina (2 a 5 profesionales, varios sillones y recepción).

**Alcance.** Se relevaron 26 sistemas con el siguiente orden de prioridad: (1) productos de origen argentino o con presencia comercial en Argentina; (2) productos latinoamericanos; (3) productos internacionales de referencia. Todas las fuentes fueron consultadas el **2026-10-03**. El informe sintetiza las fichas de relevamiento individuales ubicadas en `docs/discovery/sources/`; no se realizó investigación adicional.

---

## Metodología y limitaciones

**Fuentes.** Cada sistema cuenta con una ficha elaborada con una plantilla común (identificación, ocho áreas funcionales, modelo comercial, fortalezas, adopción y tabla numerada de fuentes con URL y fecha de consulta). Se admitieron como fuentes: sitio oficial, documentación y centros de ayuda, páginas de precios, términos y políticas, fichas de tiendas de aplicaciones y plataformas de reseñas.

**Niveles de evidencia.**
- **Comprobado (C):** la funcionalidad se observa en documentación, centro de ayuda, manual, términos o ficha de tienda con capturas.
- **Declarado (D):** la funcionalidad solo aparece como afirmación comercial (página de inicio, listados de funciones sin demostración).
- **No evidenciado:** no existe soporte público en las fuentes relevadas. Esta expresión **no significa que la funcionalidad no exista**, sino que no pudo constatarse públicamente; nunca se dedujo una funcionalidad a partir de otra.

**Limitaciones conocidas.**
1. Las páginas se leyeron mediante una herramienta de obtención web que devuelve resúmenes; algunos detalles pudieron quedar filtrados.
2. Varias calificaciones (Capterra, Google, tiendas de aplicaciones) provienen de fragmentos de buscadores y no de páginas abiertas; se las trata como **no verificadas** y no se usan como evidencia.
3. No se revisaron videos de YouTube ni la mayoría de las fichas de Capterra/GetApp.
4. Doctoralia: el dominio doctoralia.com.ar no fue accesible; la evidencia proviene de pro.doctoralia.com/ar/, clinic-cloud.com y Capterra/GetApp.
5. El país de origen de AgendaPro (Chile, según prensa) y de Doctocliq (Perú, inferido) no figura en sus sitios oficiales. Tampoco es explícito en Geblix (Argentina, inferido por teléfonos y dominio) ni en SimpleTurno (foco argentino inferido por precios en pesos y Mercado Pago).
6. Candidatos descartados: F&G Software Odontológico (error SSL), Odontiti (página truncada), Sodi (solo se halló el blog). No se perfilaron: Easy Dental, iDental, Curve Dental, CareStack, tab32, Eaglesoft, Dendoo y Medilink.
7. No se contactó a ningún proveedor ni se crearon cuentas de prueba; las demostraciones quedan fuera del alcance de esta fase.

**Advertencia sobre la puntuación.** La matriz de la sección B mide **evidencia pública**, no capacidad real. Un producto con buena documentación pública puede puntuar por encima de otro funcionalmente superior pero opaco. Las cifras de adopción y las reseñas no intervienen en la puntuación.

---

## A. Tabla comparativa

**Orden de relevancia para Argentina.** (1) Verticales odontológicos de origen argentino; (2) productos argentinos horizontales de turnos; (3) productos extranjeros con presencia argentina declarada o comprobada (sitio /ar/ o precios en ARS); (4) productos latinoamericanos sin presencia argentina evidenciada; (5) referencias internacionales. Dentro de cada grupo, se ordena por solidez de la evidencia.

### A.1 Identificación y modelo comercial

| # | Producto | Empresa | País | URL oficial | Fecha de consulta | Segmento | Modalidad | Presencia en AR | Modelo comercial |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Odonthia | Genera Impacto | Argentina | https://odonthia.com/ | 2026-10-03 | Odontólogo independiente y consultorio; equipo y sedes | SaaS (Supabase sobre AWS São Paulo) | Sí: precios en ARS | Plan gratuito sin límite de pacientes y sin tarjeta; IA ARS 20.900/mes; Max ARS 46.900/mes (USD 26/44 en LatAm); créditos de IA extra (ARS 8.400 / 36.900) |
| 2 | Bilog | Bilog (razón social: No evidenciado) | Argentina | https://bilog.com.ar/ | 2026-10-03 | Consultorios y clínicas; varios consultorios | SaaS con apps iOS/Android; modo local mencionado en términos | Sí: soporte local, más de 20 años (D) | Suscripción mensual sin permanencia ni costo de configuración (D); precios: No evidenciado (/precios 404); prueba gratuita: No evidenciado |
| 3 | DentalCore | Alfredo Di Tullio (responsable) | Argentina (La Plata) | https://dentalcore.app/ | 2026-10-03 | Consultorios y clínicas multiprofesional/multisede | SaaS | Sí: ARCA, Mercado Pago, planes de salud argentinos (D) | Plan único USD 50/mes (2 usuarios) + USD 10 por usuario; todo incluido; cobro en moneda local al tipo de cambio; garantía de 14 días |
| 4 | ClinIA | Emprinet | Argentina | https://www.clinia.com.ar/odontologia | 2026-10-03 | Odontólogos y centros; multisede | Web/nube (D) | Sí: AFIP, RENAPER, PUCO, PAMI (D); teléfono local | Precio a medida; demo gratuita; precios publicados: No evidenciado |
| 5 | DentalTec | Tándem Digital | Argentina (San Juan) | https://web.dentaltec.com.ar/ | 2026-10-03 | Odontólogos, instituciones y círculos odontológicos | SaaS web | Sí: circuito de obras sociales y círculos (D) | Licencia "por odontólogo" sin precio; mensajería WhatsApp USD 9/25/48 (50/150/300 mensajes); demo gratuita (D) |
| 6 | Órbita | Órbita Global | Argentina (La Plata) | https://hiorbita.com/ | 2026-10-03 | Consultorio, clínica y red | SaaS | Sí: clientes locales declarados; cobro en USD/ARS/USDT | Gestión: Consultorio USD 25/mes, Clínica USD 113/mes; Órbita Chat USD 150-200/mes; complementos USD 20-90; prueba gratuita: No evidenciado |
| 7 | OdontoSoft Millennium | GB Systems | Argentina (Buenos Aires) | https://gbsystems.com/os/ | 2026-10-03 | Odontólogo independiente a clínica grande | Instalación local Windows; módulo web opcional | Sí: sede en Buenos Aires | Licencia perpetua USD 390/799/1.199 o suscripción USD 35/65/99; módulo web USD 120; demo |
| 8 | OdontoApp | Sovil (Juan Segundo Sosa) | Argentina | https://odontoapp.com.ar/ | 2026-10-03 | Odontólogo independiente y consultorio | SaaS | Sí: CUIT y contacto locales | Prueba de 14 días sin tarjeta, mensual sin permanencia (C, términos); precios: No evidenciado |
| 9 | OdontoGRAMA | Solsoftware | Argentina | https://odontograma.com.ar/ | 2026-10-03 | Consultorio odontológico | SaaS | Sí: contacto local | Acceso gratuito a todas las funciones (D); precios: No evidenciado |
| 10 | OdonticLabs | ISLabs | Argentina (Villa María) | http://islabs.com.ar/OdonticLabs/ | 2026-10-03 | Consultorio y clínica; mono y multiusuario | Instalación local (modalidad exacta: No evidenciado) | Sí: soporte zonal (D) | Cotización por formulario; "sin mantenimiento mensual" (D); precios: No evidenciado |
| 11 | Geblix | Micro Fit S.A. | Argentina (inferido) | https://www.geblix.com/ | 2026-10-03 | Salud multiespecialidad, incluye odontología | SaaS | Sí: teléfonos locales | Demo gratuita a pedido (D); prueba gratuita autoservicio: No evidenciado (enlace "Empezá a probarla hoy" responde 404); precios: No evidenciado |
| 12 | SimpleTurno | 5Studios | No evidenciado (foco AR inferido) | https://simpleturno.com/rubros/odontologia | 2026-10-03 | Odontólogo independiente y pequeñas clínicas (horizontal) | SaaS web; app iOS | Precios en ARS y Mercado Pago | Gratis $0 (1 profesional); Pro $12.900/mes; sin tarjeta; cancelable |
| 13 | Turnito | No evidenciado | Argentina | https://turnito.app/ | 2026-10-03 | Profesionales y servicios (horizontal, sin vertical dental) | SaaS web | Sí: sitio /ar/, ARS | Free $0 (comisión 5 %); Plus $9.900; Advance $20.300; Pro $34.800/mes; prueba: No evidenciado |
| 14 | Dentalink | Healthatom | Chile | https://www.softwaredentalink.com/ar/ | 2026-10-03 | Consultorio y clínica; multisucursal | SaaS | Sitio /ar/ (D); línea telefónica argentina: No evidenciado | Planes Esencial/Pro/Titanium a cotizar; sin permanencia; adicionales (receta electrónica, telemedicina); prueba coordinada con ventas (D) |
| 15 | AgendaPro | AgendaPro | Chile (según prensa) | https://agendapro.com/ar/dental/software-odontologico | 2026-10-03 | Horizontal con vertical dental; multisede | SaaS; apps iOS/Android | Sí: ARS con IVA (C) | Individual ARS 13.900; Básico 33.900; Premium 44.900; Pro 314.900/mes; prueba gratuita; WhatsApp desde ARS 7.900 (50 mensajes) |
| 16 | Doctoralia (Pro / Clinic Cloud) | Doctoralia / Docplanner (grupo no confirmado) | No evidenciado | https://pro.doctoralia.com/ar/precio | 2026-10-03 | Especialistas y centros pequeños/medianos | SaaS; apps | Precios en ARS (C); sitio .com.ar no accesible | Starter ARS 25.000, Plus 35.000, VIP 55.000/mes facturado anualmente; sitio web ARS 4.000/mes; Clinic Cloud 29/49/79 EUR; prueba en AR: No evidenciado |
| 17 | DentalBox | AppLab Software LLC | EE. UU. (operación en español) | https://www.dentalbox.app/ | 2026-10-03 | Independiente a cadena (planes por boxes) | SaaS; apps nativas | Argentina en lista de países (D) | USD 24,99/39,99/59,99/89,99 (página de precios) vs. 21/33/50/75 (portada); 7 días sin tarjeta; precio en ARS: No evidenciado |
| 18 | Doctocliq | No evidenciado | Perú (inferido) | https://www.doctocliq.com/ | 2026-10-03 | Independiente, consultorio, clínica; multiespecialidad | SaaS; apps | No evidenciado | Plan gratuito (30 pacientes/mes); USD 19/29/49; 7 días sin tarjeta; complementos pagos |
| 19 | Dentidesk | DentiDesk Chile SpA | Chile | https://www.dentidesk.com | 2026-10-03 | Clínica, centro médico, gremios, facultades | SaaS; app de agenda | No evidenciado | Prueba de 15 días; precios: No evidenciado (Capterra: desde USD 50, dato del proveedor) |
| 20 | Clinicorp | Clinicorp | Brasil | https://www.clinicorp.com/ | 2026-10-03 | Consultorio a franquicias | SaaS; app del paciente | No evidenciado | R$ 159,90 / 369,90/mes; IA y Enterprise a consultar; demo; sin permanencia |
| 21 | Simples Dental | Simples Dental Software S.A. | Brasil | https://www.simplesdental.com/ | 2026-10-03 | Independiente, consultorio, clínica | SaaS; apps | No evidenciado | R$ 137,41/229,08/320,74/mes (anual); 7 días sin tarjeta; WhatsApp e IA con cargo aparte |
| 22 | Dental Office | Dental Office | Brasil | https://www.dentaloffice.com.br/ | 2026-10-03 | Independiente, consultorio, clínica, escuelas | SaaS; apps | No evidenciado | R$ 39,90 a 298,54/mes; prueba de 7 días |
| 23 | Agendit | Agendit | Paraguay | https://agendit.com.py/ | 2026-10-03 | Horizontal (belleza, bienestar, salud) | SaaS | No evidenciado | Gs 110.000 a 660.000/mes; prueba: No evidenciado |
| 24 | Open Dental | Open Dental Software | EE. UU. | https://www.opendental.com/ | 2026-10-03 | Prácticas de cualquier tamaño | Local (.NET) + servicios en nube | No evidenciado | USD 89/mes por ubicación ("otros países"); eServices USD 5-165; prueba y garantía de 90 días |
| 25 | Dentrix | Henry Schein One | EE. UU. | https://www.dentrix.com/ | 2026-10-03 | Consultorio a grupos multisede | Nube e instalación local | No evidenciado | Precios: No evidenciado (requiere demo) |
| 26 | Odontonet | Aseting Informática S.L. | España | https://www.odontonet.es/ | 2026-10-03 | Clínica dental | SaaS | No evidenciado | Precios: No evidenciado; módulos con descuentos de hasta 50 %; prueba: No evidenciado |

### A.2 Capacidades por área

Leyenda: **C** = comprobado; **D** = declarado; "No evidenciado" = sin soporte público. "C (módulo)" indica que solo consta el nombre del módulo en un catálogo, sin descripción.

| # | Producto | Agenda | Turnos digitales | Automatización | Clínica odontológica | Administración | Integraciones | Operación | Seguridad y cumplimiento AR |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Odonthia | C: vistas día/semana/mes, columna por profesional, capacidad por sede que impide solapamientos, duración variable, bloqueos, sobreturno con alerta, sala de espera | C: reserva online con aprobación, enlace/QR, confirmación y cancelación por enlace de WhatsApp | C: recordatorio WhatsApp con texto precargado (envío manual); D: WhatsApp automático en planes pagos | C: firma remota con hash SHA-256; D: odontograma FDI, periodontograma, presupuestos, ortodoncia, IA | C: seña al agendar; D: caja y reportes; ARCA, MP, obras sociales: No evidenciado | D: WhatsApp Business, Google/Apple/Outlook Calendar, importación CSV; ARCA/MP: No evidenciado | C: sedes, roles (Titulares, Profesionales, Administrativos), exportación Excel, documentación pública; auditoría general: No evidenciado | C: TLS, AES-256, respaldos diarios, retención de 10 años (Ley 26.529), datos en Brasil; Ley 25.326: No evidenciado |
| 2 | Bilog | C: vista diaria/semanal, copiar/mover turnos; sillones, bloqueos y solapamientos: No evidenciado | D: agenda online, registro por QR (la sección existe en ayuda, sin detalle) | D: recordatorios y confirmaciones por WhatsApp/SMS | C: historia clínica, odontograma, presupuestos, órdenes de laboratorio; D: IA iAngela para radiografías | C: caja, liquidaciones a obras sociales y profesionales (secciones), facturación electrónica, reportes; MP: No evidenciado | D: WhatsApp/SMS; ARCA explícito, MP, API: No evidenciado | C: exportación CSV al cancelar, centro de ayuda; D: multiconsultorio; roles y auditoría: No evidenciado | C: cita Ley 25.326, respaldos en nube, controles de acceso genéricos; Ley 26.529: No evidenciado |
| 3 | DentalCore | D: multiprofesional con arrastrar y soltar, sala de espera virtual; sillones y solapamientos: No evidenciado | D: portal con reserva y cancelación, bot de WhatsApp, chatbot IA | D: 9 automatizaciones de WhatsApp (confirmación, relleno de huecos, recalls) | D: odontograma, periodontograma, CDSS, presupuestos versionados, consentimientos | D: ARCA, MP con QR, caja, más de 20 planes de salud precargados | D: WhatsApp, ARCA, MP, HL7 FHIR | C: descarga de datos 30 días tras la baja; D: multisucursal, auditoría de accesos; roles: No evidenciado | C: Ley 25.326 y AAIP, cifrado en tránsito y reposo, datos posiblemente fuera de AR; Ley 26.529 solo D |
| 4 | ClinIA | C (módulo): Agenda; detalle: No evidenciado | C (módulo): Turnos Online; D: agendado con IA por WhatsApp | D: recordatorios por WhatsApp y correo | D: odontograma 3D, historia clínica, presupuestos, receta electrónica (ReNaPDiS, HL7 FHIR); C (módulo): periodontograma, imágenes | C (módulo): caja, facturación; D: AFIP, obras sociales con PUCO, PAMI, SUMAR+ | D: AFIP, RENAPER, PUCO, SIGIPSA, WhatsApp, HL7 FHIR | C (módulo): sucursales, roles, auditoría, exportación | C: HTTPS, acceso por rol, Ley 25.326, canal de vulnerabilidades; respaldos y Ley 26.529: No evidenciado |
| 5 | DentalTec | D: franjas por odontólogo; resto: No evidenciado | D: confirmaciones por WhatsApp; reserva online: No evidenciado | D: recordatorios por WhatsApp | D: historia clínica, odontograma con CIE-10; periodontograma y presupuestos: No evidenciado | D: facturación ARCA, validación de prácticas contra obras sociales, liquidación multinivel | D: ARCA, 14+/15+ obras sociales vía SOAP, WhatsApp | D: 10 roles, auditoría total, soporte 24/7; exportación: No evidenciado | D: JWT, bcrypt, respaldo automático; leyes argentinas y política de privacidad: No evidenciado |
| 6 | Órbita | D: agenda por sillón, oferta inteligente de turnos; C: planes por cantidad de profesionales | D: reserva por WhatsApp 24/7, triage de urgencias con IA; C: turnero físico (complemento) | D: recordatorios, recontacto de ausentes; C: módulo de marketing por créditos | D: odontograma, periodontograma, historia clínica firmada, dictado por voz | D: facturación, caja, obras sociales; MP y liquidaciones: No evidenciado | D: compatibilidad con Dentalink, Bilog y Benty; WhatsApp | C: sedes por plan; D: migración gratuita; roles y auditoría: No evidenciado | No evidenciado (política de privacidad con error 404) |
| 7 | OdontoSoft Millennium | C: vistas 1 día/2 días/semana, colores, asistencia, restricción por odontólogo; sillones y bloqueos: No evidenciado | C: SMS masivo para confirmaciones; reserva online: No evidenciado | C: SMS masivo manual por filtros; recordatorios automáticos: No evidenciado | C: odontograma, periodontograma (índice O'Leary), presupuestos por plan | C: cobros, cuentas, listas de obras sociales, liquidación de profesionales, más de 20 reportes; ARCA: No evidenciado | C: SMS propio, módulo web; WhatsApp, MP, ARCA: No evidenciado | C: roles y permisos, auditoría, multisede vía web; D: exportación | C: control de acceso, auditoría; leyes argentinas: No evidenciado |
| 8 | OdontoApp | D: agenda digital | No evidenciado | D: recordatorios automáticos (canal: No evidenciado) | D: historia clínica, odontograma; C (términos): carga de imágenes | No evidenciado | No evidenciado | C: exportación o eliminación a pedido, soporte WhatsApp/correo | C: Ley 25.326 (arts. 9, 14, 16), propiedad del dato; D: cifrado en tránsito; respaldo: No evidenciado |
| 9 | OdontoGRAMA | D: agendas personalizables con control de asistencia | No evidenciado | No evidenciado | D: fichas con imágenes, tratamientos y diagnósticos; odontograma: No evidenciado | D: caja, cuentas por cobrar, facturación a obras sociales, estadísticas | No evidenciado | C: contacto por correo y WhatsApp; resto: No evidenciado | D: nube 24/7; términos y privacidad: No evidenciado |
| 10 | OdonticLabs | D: estados por color | No evidenciado | No evidenciado | D: ficha, odontograma automático, fotos, presupuestos, laboratorio | D: facturación, obras sociales, caja por odontólogo, inventario | No evidenciado | D: soporte zonal 24 h | No evidenciado |
| 11 | Geblix | D: vistas día/semana/mes, salas de espera | D: chatbot IA multicanal, videoconsulta | D: recordatorios WhatsApp/SMS/correo, campañas | D: historia clínica genérica; odontograma: No evidenciado | D: finanzas, cobros online, reportes | D: WhatsApp, SMS y correo como canales | D: exportación al cancelar, soporte telefónico local | D: "segura", sin detalle; leyes argentinas: No evidenciado |
| 12 | SimpleTurno | D: detección automática de conflictos, multiprofesional (Pro) | D: enlace de reserva, asistente IA, WhatsApp prearmado | D: recordatorios por correo; WhatsApp 60/mes (Pro) | No evidenciado (historia clínica fuera de alcance según el sitio) | D: seña con MP, analítica | D: MP, Google Calendar, WhatsApp | D: soporte prioritario; roles, auditoría y exportación: No evidenciado | D: "cifrado de nivel bancario"; privacidad con error 404 |
| 13 | Turnito | D: múltiples agendas, duraciones personalizables, turnos recurrentes | D: reserva 24/7 sin registro, WordPress, Google Meet | D: recordatorios WhatsApp/correo/Telegram con cupos | D: ficha de clientes (Pro); odontograma: No evidenciado | D: cobros MP/PayPal/Talo, seña, comisión por transacción | D: Google Calendar bidireccional, MP, Talo, WhatsApp, Telegram | No evidenciado | No evidenciado |
| 14 | Dentalink | C (ayuda): horarios por profesional, reagendamiento masivo, Google Calendar; sillones, bloqueos y solapamientos: No evidenciado | C: confirmación/cancelación, notificaciones por WhatsApp, campañas de agendamiento; D: agendamiento online, contact center con IA | C: notificaciones automáticas, CRM, encuestas; D: recordatorios 1 a 3 días antes | C (ayuda): odontograma, periodontograma, planes, consentimientos, firma digital, presupuestos; D: IA para radiografías | C: caja, cuotas, liquidaciones, convenios de obras sociales, inventario, esterilización; ARCA y MP: No evidenciado | C: Google Calendar, WhatsApp; API, ARCA y MP: No evidenciado | C: roles y permisos, carga masiva, exportación de reportes a Excel; D: multisucursal | D: políticas enlazadas (no relevadas); leyes argentinas: No evidenciado |
| 15 | AgendaPro | D: agenda 24/7, multiprofesional y multisede; C: planes de 1 y de 2 a 20 profesionales | D: reserva sin registro, marketplace, doble confirmación, seña; C: sitio web en Premium | D: recordatorios WhatsApp/SMS/correo; C: WhatsApp como complemento pago, emailing por plan | D: ficha clínica, presupuestos; odontograma: No evidenciado | D: caja, comisiones, reportes; C: facturación electrónica AR "Próximamente"; obras sociales: No evidenciado | C: API (plan Pro), Google Analytics/Meta Pixel; D: MP (respaldo débil) | C: apps iOS/Android, centro de ayuda; auditoría y exportación: No evidenciado | D: nube, videoconsulta cifrada; leyes argentinas: No evidenciado |
| 16 | Doctoralia | D: duración configurable, múltiples sitios, días no laborables; sillones y solapamientos: No evidenciado | D: reserva 24/7 desde perfil, Google y redes; confirmar/cancelar/reprogramar por WhatsApp; lista de espera (VIP) | D: recordatorios correo/push/SMS/WhatsApp, campañas SMS | D: historia clínica (Plus); odontograma y periodontograma solo en Clinic Cloud Max | D: facturación orientada a España (Clinic Cloud); en AR: No evidenciado | D: Doctoralia-Clinic Cloud, Google My Business; MP y ARCA: No evidenciado | D: multisitio, onboarding; roles: No evidenciado | D: RGPD y auditoría (Clinic Cloud); leyes argentinas: No evidenciado |
| 17 | DentalBox | C: vista por box y por profesional, mover citas arrastrando, impide agendar en el pasado; D: bloques recurrentes, multibox; solapamientos: No evidenciado | D: página de reserva, pre check-in, autogestión desde el mensaje, lista de espera | D: recordatorios por correo y WhatsApp, confirmación visible en agenda | C: odontograma por diente y cara vinculado a presupuesto y plan; D: anamnesis, CBCT, periodontograma | C: caja del día, pagos parciales, deudas; D: facturación Chile/México; ARCA: No evidenciado | D: WhatsApp, Haulmer, Facturapi, CBCT; MP no verificado | D: roles granulares, auditoría, multisede (Premium) | D: TLS, AES-256, respaldos diarios, RGPD/LGPD; leyes argentinas: No evidenciado |
| 18 | Doctocliq | D: Google Calendar; un médico en el plan gratuito | D: confirmaciones, Soyla IA (pago); reserva online: No evidenciado | D: recordatorios WhatsApp/correo/SMS, marketing pago | D: historia clínica, odontograma, periodontograma, presupuestos, consentimientos | D: caja, facturación (PE/MX/CO/EC/RD), pagos en línea | D: Google Calendar, WhatsApp, Meta Business Partner; integraciones AR: No evidenciado | D: soporte por chat y correo; resto: No evidenciado | No evidenciado |
| 19 | Dentidesk | D: calendario personalizable, estados, multisede | D: reserva online; C: WhatsApp no disponible al momento del artículo oficial | D: recordatorios por correo, encuestas | C: anamnesis y odontograma (nomenclaturas); D: formularios por especialidad, imágenes, presupuestos | D: facturación SII/Alegra, reportes, liquidación de honorarios | D: SII, Alegra; integraciones AR: No evidenciado | D: usuarios y permisos, migración asistida | No evidenciado |
| 20 | Clinicorp | D: agenda inteligente, check-in por QR, alertas de retorno | D: reserva online (Premium), agente IA de WhatsApp (agendar, reprogramar, cancelar), app del paciente | D: confirmaciones, seguimiento de ausentes, recuperación de cobros | D: historia clínica, anamnesis con firma, planes, integración radiológica; odontograma: No evidenciado | D: Clinipay (Pix, boleto, tarjeta) con tarifas publicadas, conciliación (Brasil) | D: WhatsApp, Google Meu Negócio, centros radiológicos | D: usuarios ilimitados con niveles, migración | D: LGPD; leyes argentinas: No evidenciado |
| 21 | Simples Dental | D: agenda online con confirmación por WhatsApp, Alexa | D: enlaces de reserva 24 h, sitio de la clínica, secretaria IA (pago) | D: confirmaciones WhatsApp (pago), campañas, alertas de retorno | D: prontuario con odontograma, anamnesis, firma electrónica, ortodoncia | D: flujo de caja, comisiones, Pix/boleto, terminal integrada (Brasil) | D: Asaas, Meta Business Partner, API (según Capterra) | D: centro de ayuda, capacitación en vivo | D: LGPD, respaldos; leyes argentinas: No evidenciado |
| 22 | Dental Office | D: varios dentistas, salas/sillones, estados por color, faltas, lista de espera | D: reserva por enlace, confirmación por WhatsApp Business | D: recordatorios WhatsApp/SMS/correo, alertas de retorno, CRM | D: prontuario por especialidad, asistente de voz; odontograma: No evidenciado | D: finanzas, comisiones, Pix/boleto (Brasil) | D: WhatsApp Business, pagos, software contable | No evidenciado | D: LGPD; leyes argentinas: No evidenciado |
| 23 | Agendit | D: multiprofesional por plan, Google Calendar contra doble reserva (Full) | D: sitio de reservas, agente IA MIA en WhatsApp, Google Meet | D: recordatorios por correo y WhatsApp con cupo, fidelización | D: ficha clínica genérica (Premium); odontograma: No evidenciado | D: pagos QR/tarjeta, caja, facturación electrónica (Paraguay) | D: Google Calendar/Meet, WhatsApp | D: soporte por WhatsApp | No evidenciado |
| 24 | Open Dental | C: vistas día/semana, operatorios (sillones), horarios por profesional, bloqueos, superposición solo si se habilita, Pinboard, segundo proveedor por cita | C: Web Sched (4 módulos), lista ASAP con enlace único, eConfirmations; WhatsApp: No evidenciado | C: eReminders, mensajería de texto integrada, Web Sched Recall; D: correo masivo | C: planes de tratamiento en agenda; D: odontograma 3D, recetas, imágenes | D: estados de cuenta, Message-to-Pay, cámaras de compensación de EE. UU. | D: cientos de bridges, conversión desde más de 200 sistemas; integraciones AR: No evidenciado | C: gestión de clínicas; D: soporte telefónico; roles y auditoría: No evidenciado (página 404) | No evidenciado |
| 25 | Dentrix | D: programación multiubicación | D: Reserve with Google, texto bidireccional | D: recordatorios, campañas por texto y correo | D: imágenes con IA, notas de voz, formularios de admisión; odontograma: No evidenciado | D: seguros de EE. UU., facturación al paciente, KPI | D: API Exchange, Reserve with Google | D: multiubicación, soporte, capacitación | D: respaldo y ciberseguridad gestionados; leyes argentinas: No evidenciado |
| 26 | Odontonet | D: agenda, sala de espera, 3 puestos en configuración base | D (módulos): portal con reserva 24/7, WhatsApp | D: recordatorios SMS/WhatsApp, fidelización | D: odontograma, periodontograma, radiografía, presupuestos, firma, recetas | D: facturación Verifactu, mutuas, pagos con tarjeta, BI (España) | D: WhatsApp, VoIP, pagos, radiología | D: multicentro, roles, migración | D: RGPD, copias automáticas, roles; leyes argentinas: No evidenciado |

### A.3 Fortalezas, limitaciones, diferenciales y evidencia de adopción

Las cifras de clientes son siempre **declaradas por el proveedor**. Solo se consignan reseñas cuya página fue efectivamente consultada; las provenientes de fragmentos de buscador figuran como "No evidenciado".

| # | Producto | Fortalezas | Limitaciones | Diferenciales | Evidencia de adopción |
|---|---|---|---|---|---|
| 1 | Odonthia | Documentación pública detallada de agenda, reserva online, sedes y roles; plan gratuito; precios en ARS; exportación y respaldos comprobados | Recordatorio de WhatsApp manual en la documentación; sin ARCA, MP ni obras sociales; datos alojados en Brasil; no cita la Ley 25.326 | Control de capacidad por sede que impide solapamientos (C); reserva con aprobación; firma con hash SHA-256 | 2.714 consultorios (declarado por el proveedor); reseñas: No evidenciado |
| 2 | Bilog | Trayectoria declarada de más de 20 años; app nativa; ayuda pública con caja, liquidaciones y presupuestos; términos con Ley 25.326 | Sin precios ni prueba; roles y auditoría no evidenciados; reserva online solo declarada | Liquidación a obras sociales y profesionales; IA iAngela (D) | Más de 1.500 clínicas y 5.000 usuarios (declarado por el proveedor); App Store AR 3,5/5 con 15 valoraciones, con quejas tras una actualización |
| 3 | DentalCore | Precio único publicado y todo incluido; privacidad detallada con Ley 25.326 y AAIP; paquete funcional amplio | Producto "por lanzar"; casi todo declarado; precio en USD; datos posiblemente fuera de AR; FAQ de seguridad sin respuestas | CDSS basado en reglas; creado por un odontólogo en ejercicio (D) | Clientes: No evidenciado (adoptantes tempranos); reseñas: No evidenciado |
| 4 | ClinIA | Catálogo funcional público; integraciones con padrones oficiales; página de seguridad con límites explícitos | Sin precios; catálogo sin detalle; reserva online no demostrada | Receta electrónica (ReNaPDiS, HL7 FHIR) y verificación de cobertura vía PUCO (D) | "Cientos de odontólogos" (declarado por el proveedor); reseñas: No evidenciado |
| 5 | DentalTec | Foco en el circuito de obras sociales y círculos; precios de mensajería publicados | Contenido casi exclusivamente declarado; sin precio de licencia; sin privacidad ni términos visibles; cifras inconsistentes de obras sociales | Validación de prácticas en tiempo real y cierre multinivel hacia círculos (D) | Más de 2.000 profesionales y 30 instituciones (declarado por el proveedor); reseñas: No evidenciado |
| 6 | Órbita | Precios públicos detallados; migración gratuita; propuesta centrada en WhatsApp | Sin política de privacidad legible; precios en USD; funciones "próximamente" | Capa de WhatsApp sobre sistemas existentes (Dentalink, Bilog, Benty); triage de urgencias con IA (D) | Más de 12 clientes destacados y métricas de 30 días (declarado por el proveedor); reseñas: No evidenciado |
| 7 | OdontoSoft Millennium | Clínica y administración comprobadas (odontograma, periodontograma, liquidaciones, obras sociales); precios publicados; licencia perpetua | Instalación local en Windows; sin reserva online ni recordatorios automáticos; precios en USD | Licencia perpetua o suscripción con profesionales ilimitados; SMS masivo | Más de 3.000 dentistas y clínicas (declarado por el proveedor); reseñas: No evidenciado |
| 8 | OdontoApp | Términos y privacidad claros con Ley 25.326 y propiedad del dato; prueba de 14 días | Funcionalidad publicada mínima; sin precios verificados; sin política de respaldo | No evidenciado | Más de 10 odontólogos (declarado por el proveedor); reseñas: No evidenciado |
| 9 | OdontoGRAMA | Acceso gratuito para evaluar; administración básica con obras sociales | Sitio mínimo; sin precios, ayuda, términos ni privacidad | No evidenciado | Clientes: No evidenciado; reseñas: No evidenciado |
| 10 | OdonticLabs | Alcance clínico-administrativo declarado amplio para un producto local | Sin turnos digitales; sin precios, capturas ni seguridad; páginas internas 404 | Instalación local mono/multiusuario sin abono mensual (D) | Clientes: No evidenciado; reseñas: No evidenciado |
| 11 | Geblix | Proveedor local con soporte telefónico; exportación declarada | Sin funciones odontológicas específicas; sin precios; casi todo declarado | Chatbot de IA y videoconsulta (D) | Más de 7 millones de turnos (declarado por el proveedor); reseñas: No evidenciado |
| 12 | SimpleTurno | Plan gratuito permanente; sin comisión; seña con MP | No es un sistema clínico; cupo de 60 mensajes de WhatsApp; sin roles ni cumplimiento | Vertical dental dentro de un producto horizontal de bajo costo | Clientes: No evidenciado; reseñas: No evidenciado |
| 13 | Turnito | Plan gratuito; precios en ARS; varios medios de pago locales | Horizontal sin funciones dentales; comisión por transacción; sin seguridad evidenciada | Seña con múltiples pasarelas y Google Meet automático (D) | Testimonios en el sitio (declarado por el proveedor); reseñas Google: No evidenciado (cifra declarada por el sitio, no verificada) |
| 14 | Dentalink | Centro de ayuda extenso; cobertura clínica y administrativa amplia | Sin precios; sin ARCA ni MP; sin línea de soporte argentina evidenciada | Funciones de IA (D); módulos de ortodoncia y estética | Más de 15.000 clientes y 12 millones de pacientes (declarado por el proveedor); reseñas: No evidenciado (solo fragmento de buscador) |
| 15 | AgendaPro | Precios en ARS escalonados; apps; centro de ayuda | Horizontal sin odontograma; WhatsApp con cargo aparte; facturación AR "próximamente" | Marketplace de pacientes y marketing integrado (D) | Más de 135.000 profesionales o 150.000 según la página (declarado por el proveedor, inconsistente); reseñas: No evidenciado (solo fragmento de buscador) |
| 16 | Doctoralia | Marketplace con reservas y reseñas de pacientes; precios en ARS | Pago anual; funciones dentales solo en Clinic Cloud Max; facturación orientada a España; sitio AR no verificado | Lista de espera automática y operaciones masivas (VIP) (D) | Capterra 4,7/5 con 415 reseñas (GetApp igual); Clinic Cloud: más de 12.000 profesionales (declarado por el proveedor) |
| 17 | DentalBox | Agenda por box y profesional; odontograma integrado a presupuesto; prueba sin tarjeta | Sin integraciones argentinas; precios inconsistentes; multisede y soporte solo en Premium | IA con acceso a datos, CBCT, telemedicina (D) | Clientes: No evidenciado; reseñas: No evidenciado |
| 18 | Doctocliq | Plan gratuito permanente; precios bajos; periodontograma declarado | Sin presencia ni funciones para Argentina; límites de pacientes | Asistente Soyla IA para WhatsApp (D) | Más de 4.000 médicos (declarado por el proveedor); reseñas: No evidenciado |
| 19 | Dentidesk | Cobertura clínica amplia; reportería; oferta académica | WhatsApp no disponible; sin precios; sin presencia en AR | Línea para facultades y gremios (D) | Clientes: No evidenciado; App Store CL 5,0 con 4 calificaciones; Capterra sin reseñas |
| 20 | Clinicorp | Alcance amplio; pasarela propia con tarifas publicadas; precio de entrada publicado | Agenda sin demostración; sin español ni Argentina | Agentes de IA en WhatsApp para agendar y recuperar ausentes (D) | Más de 32.000 clínicas (declarado por el proveedor); reseñas: No evidenciado (Reclame Aqui solo vía buscador) |
| 21 | Simples Dental | Producto maduro; precios claros; prontuario con firma electrónica | Sin español ni funciones AR; WhatsApp e IA con cargo aparte | Secretaria IA, Alexa, scoring de crédito (D) | Más de 19.000 clínicas (declarado por el proveedor); App Store consultada 3,5 con 2 calificaciones; Capterra 4,7 con 3 reseñas |
| 22 | Dental Office | Entrada muy económica; prueba de 7 días; lista de espera declarada | Todo declarado; sin odontograma; sin AR | Versión para escuelas de odontología (D) | Más de 90.000 dentistas (declarado por el proveedor); Reclame Aqui 7,3/10 con quejas de cobro y soporte; Google: No evidenciado (solo buscador) |
| 23 | Agendit | Precios escalonados; WhatsApp incluido con cupo | Horizontal sin funciones dentales; sin presencia AR | Agente IA MIA y programa de fidelización (D) | Testimonios de dos clínicas paraguayas (declarado por el proveedor); reseñas: No evidenciado |
| 24 | Open Dental | Agenda mejor documentada del relevamiento; reserva online modular con precios | Orientado a EE. UU.; sin WhatsApp; cargos por mensaje; seguridad no evidenciada | Lista ASAP con enlace único para tomar huecos; segundo proveedor por cita | Clientes: No evidenciado; reseñas: No evidenciado (fragmento de buscador con cifras discrepantes) |
| 25 | Dentrix | Ecosistema amplio respaldado por Henry Schein One | Sin precios; orientado a seguros de EE. UU.; sin presencia AR | Escala declarada; IA de imágenes (D) | Más de 35.000 prácticas (declarado por el proveedor); reseñas: No evidenciado (solo fragmento de buscador) |
| 26 | Odontonet | Modelo modular; cobertura clínica declarada amplia | Reserva y WhatsApp como módulos con costo no publicado; orientado a España | Cumplimiento fiscal español (Verifactu) (D) | Testimonios de clínicas; reseñas: No evidenciado |

Fuentes detalladas por sistema: `docs/discovery/sources/<slug>.md` (slugs: odonthia, bilog, dentalcore, clinia, dentaltec, orbita, odontosoft-millennium, odontoapp, odontograma, odonticlabs, geblix, simpleturno, turnito, dentalink, agendapro, doctoralia, dentalbox, doctocliq, dentidesk, clinicorp, simples-dental, dental-office, agendit, open-dental, dentrix, odontonet).

---

## B. Matriz de puntuación (0 a 5)

### B.1 Rúbrica basada en evidencia

| Puntaje | Criterio |
|---|---|
| 0 | No evidenciado |
| 1 | Declarado aislado (un único ítem del criterio, sin demostración) |
| 2 | Declarado parcial (varios ítems) o un ítem comprobado aislado |
| 3 | Declarado amplio (la mayoría de los ítems) o comprobado parcial (varios ítems comprobados) |
| 4 | Comprobado en la mayoría de los ítems del criterio |
| 5 | Comprobado completo y con un diferencial evidenciado |

**Reglas de aplicación:**
1. **Tope por declaración:** un criterio sustentado solo en evidencia "Declarado" no puede superar 3.
2. **Nombre de módulo sin descripción** (p. ej., un catálogo que solo lista "Agenda") cuenta como declarado. Un título de artículo de ayuda que nombra una función concreta (p. ej., "Integra Dentalink con Google Calendar") cuenta como comprobado parcial.
3. **Integraciones locales y WhatsApp:** para superar 2 se requiere al menos una integración argentina (ARCA/AFIP, Mercado Pago u otra pasarela local, obras sociales o padrones oficiales).
4. **Administración:** las funciones atadas exclusivamente a sistemas fiscales o de pago de otro país (Pix, SII, Verifactu, seguros de EE. UU.) puntúan como máximo 2, por no ser aplicables en Argentina.
5. **Precio y facilidad de adopción** (sub-rúbrica): 0 = nada publicado; 1 = solo demo o cotización; 2 = prueba gratuita o precios parciales; 3 = precios completos publicados (en cualquier moneda); 4 = precios publicados más prueba o plan gratuito, en ARS o con cobro en moneda local; 5 = plan gratuito permanente, precios en ARS y sin tarjeta ni permanencia.
6. Las cifras de adopción y las reseñas **no** intervienen en el puntaje.

**Advertencia:** el puntaje mide la **evidencia pública disponible**, no la capacidad real del producto.

### B.2 Matriz

Ponderaciones: T = Gestión de turnos y automatización (25 %); CL = Funcionalidad odontológica clínica (20 %); I = Integraciones locales y WhatsApp (15 %); A = Administración, cobros y facturación (15 %); P = Experiencia del paciente (10 %); S = Seguridad, exportación y trazabilidad (10 %); $ = Precio y facilidad de adopción (5 %).

Total ponderado = Σ (puntaje × peso). La columna "Desglose" muestra cada producto puntaje × peso en el orden T, CL, I, A, P, S, $.

| Rank | Producto | T | CL | I | A | P | S | $ | Desglose (Σ puntaje × peso) | Total |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Odonthia | 5 | 3 | 2 | 2 | 4 | 4 | 5 | 1,25 + 0,60 + 0,30 + 0,30 + 0,40 + 0,40 + 0,25 | 3,50 |
| 2 | DentalCore | 3 | 3 | 3 | 3 | 3 | 4 | 4 | 0,75 + 0,60 + 0,45 + 0,45 + 0,30 + 0,40 + 0,20 | 3,15 |
| 3 | Dentalink | 3 | 4 | 2 | 4 | 3 | 2 | 1 | 0,75 + 0,80 + 0,30 + 0,60 + 0,30 + 0,20 + 0,05 | 3,00 |
| 4 | Open Dental | 5 | 3 | 1 | 2 | 4 | 1 | 3 | 1,25 + 0,60 + 0,15 + 0,30 + 0,40 + 0,10 + 0,15 | 2,95 |
| 5 | Bilog | 3 | 3 | 2 | 4 | 2 | 3 | 1 | 0,75 + 0,60 + 0,30 + 0,60 + 0,20 + 0,30 + 0,05 | 2,80 |
| 6 | DentalBox | 3 | 3 | 1 | 3 | 3 | 3 | 3 | 0,75 + 0,60 + 0,15 + 0,45 + 0,30 + 0,30 + 0,15 | 2,70 |
| 7 | OdontoSoft Millennium | 2 | 4 | 1 | 4 | 1 | 3 | 3 | 0,50 + 0,80 + 0,15 + 0,60 + 0,10 + 0,30 + 0,15 | 2,60 |
| 8 | ClinIA | 2 | 3 | 3 | 3 | 2 | 3 | 1 | 0,50 + 0,60 + 0,45 + 0,45 + 0,20 + 0,30 + 0,05 | 2,55 |
| 9 | Clinicorp | 3 | 3 | 2 | 2 | 3 | 1 | 3 | 0,75 + 0,60 + 0,30 + 0,30 + 0,30 + 0,10 + 0,15 | 2,50 |
| 9 | Simples Dental | 3 | 3 | 2 | 2 | 3 | 1 | 3 | 0,75 + 0,60 + 0,30 + 0,30 + 0,30 + 0,10 + 0,15 | 2,50 |
| 11 | Odontonet | 3 | 3 | 2 | 2 | 2 | 2 | 1 | 0,75 + 0,60 + 0,30 + 0,30 + 0,20 + 0,20 + 0,05 | 2,40 |
| 12 | AgendaPro | 3 | 2 | 2 | 2 | 3 | 1 | 4 | 0,75 + 0,40 + 0,30 + 0,30 + 0,30 + 0,10 + 0,20 | 2,35 |
| 13 | Dental Office | 3 | 2 | 2 | 2 | 3 | 1 | 3 | 0,75 + 0,40 + 0,30 + 0,30 + 0,30 + 0,10 + 0,15 | 2,30 |
| 14 | Órbita | 3 | 2 | 3 | 2 | 2 | 0 | 3 | 0,75 + 0,40 + 0,45 + 0,30 + 0,20 + 0,00 + 0,15 | 2,25 |
| 15 | Dentrix | 3 | 2 | 2 | 2 | 3 | 1 | 1 | 0,75 + 0,40 + 0,30 + 0,30 + 0,30 + 0,10 + 0,05 | 2,20 |
| 15 | DentalTec | 2 | 2 | 3 | 3 | 1 | 2 | 2 | 0,50 + 0,40 + 0,45 + 0,45 + 0,10 + 0,20 + 0,10 | 2,20 |
| 17 | Doctoralia | 3 | 2 | 2 | 1 | 3 | 1 | 3 | 0,75 + 0,40 + 0,30 + 0,15 + 0,30 + 0,10 + 0,15 | 2,15 |
| 18 | Turnito | 3 | 1 | 3 | 2 | 2 | 0 | 4 | 0,75 + 0,20 + 0,45 + 0,30 + 0,20 + 0,00 + 0,20 | 2,10 |
| 19 | SimpleTurno | 3 | 0 | 3 | 2 | 2 | 1 | 5 | 0,75 + 0,00 + 0,45 + 0,30 + 0,20 + 0,10 + 0,25 | 2,05 |
| 20 | Doctocliq | 2 | 3 | 2 | 2 | 1 | 0 | 3 | 0,50 + 0,60 + 0,30 + 0,30 + 0,10 + 0,00 + 0,15 | 1,95 |
| 21 | Agendit | 3 | 1 | 2 | 2 | 2 | 0 | 3 | 0,75 + 0,20 + 0,30 + 0,30 + 0,20 + 0,00 + 0,15 | 1,90 |
| 22 | Dentidesk | 2 | 3 | 1 | 2 | 1 | 0 | 2 | 0,50 + 0,60 + 0,15 + 0,30 + 0,10 + 0,00 + 0,10 | 1,75 |
| 23 | Geblix | 2 | 1 | 1 | 2 | 2 | 1 | 1 | 0,50 + 0,20 + 0,15 + 0,30 + 0,20 + 0,10 + 0,05 | 1,50 |
| 24 | OdonticLabs | 1 | 3 | 0 | 3 | 0 | 0 | 1 | 0,25 + 0,60 + 0,00 + 0,45 + 0,00 + 0,00 + 0,05 | 1,35 |
| 25 | OdontoGRAMA | 1 | 2 | 0 | 3 | 0 | 1 | 2 | 0,25 + 0,40 + 0,00 + 0,45 + 0,00 + 0,10 + 0,10 | 1,30 |
| 26 | OdontoApp | 1 | 2 | 0 | 0 | 0 | 3 | 2 | 0,25 + 0,40 + 0,00 + 0,00 + 0,00 + 0,30 + 0,10 | 1,05 |

Los empates (puestos 9 y 15) se mantienen como puestos compartidos.

### B.3 Notas sobre puntajes no evidentes

- **Odonthia y Open Dental (T = 5):** son los únicos con la agenda comprobada en documentación pública, incluidos sillones u operatorios, bloqueos y control de superposición. En Odonthia, la superposición se impide por capacidad de sede y el sobreturno exige forzar una alerta; en Open Dental, la superposición en un operatorio solo ocurre si se la habilita.
- **DentalCore (2.º puesto):** asciende por una combinación de amplitud declarada (tope 3 en cinco criterios) y documentos legales comprobados (S = 4). Es un producto "por lanzar": su posición refleja documentación, no madurez ni adopción, y debe leerse con cautela.
- **Dentalink (CL = 4, A = 4):** los títulos del centro de ayuda describen funciones concretas (odontograma, periodontograma, liquidaciones, convenios), lo que constituye evidencia comprobada parcial. En precio ($ = 1), Dentalink no publica valores (cotización a pedido) y la prueba se coordina con ventas, por lo que no constituye una prueba gratuita autoservicio; el precio de USD 29 informado por Capterra es un dato de terceros no verificado en la fuente oficial y no se computa.
- **Geblix ($ = 1):** el sitio oficial solo ofrece "Solicitá una demo gratis" y contacto con un asesor; no publica precios. El botón "¡Empezá a probarla hoy!" de microfit.com.ar apunta a https://www.geblix.com/inicio/referral, que respondió HTTP 404 al 2026-10-03, por lo que la prueba gratuita autoservicio no está evidenciada.
- **Bilog (A = 4):** el índice de ayuda y la ficha de App Store comprueban caja, liquidaciones, facturación electrónica y seguimiento de pagos.
- **OdontoSoft Millennium (T = 2):** la ausencia de reserva online está comprobada en la documentación del módulo web y el SMS es de envío manual.
- **Doctoralia (A = 1):** la facturación evidenciada (Clinic Cloud) responde a normativa española; para Argentina no hay evidencia.

---

## C. Análisis competitivo

### C.1 Funcionalidades ya estándar en el mercado

1. **Recordatorios y confirmaciones por WhatsApp.** Son declarados por la gran mayoría de los sistemas relevados (Bilog, Dentalink, DentalTec, ClinIA, DentalCore, Órbita, AgendaPro, Doctoralia, DentalBox, Clinicorp, Simples Dental, Dental Office, entre otros). Sin embargo, solo Dentalink (notificaciones automáticas en ayuda) y Odonthia (enlace con texto precargado) lo tienen comprobado. Ningún perfil evidencia el uso de la API oficial de WhatsApp Business.
2. **Agenda multiprofesional en la nube.** Es la base de casi todos los productos, aunque en la mayoría solo está declarada. Se comprueba en Odonthia, Open Dental, Dentalink (horarios por profesional), DentalBox y OdontoSoft.
3. **Reserva online por enlace o página propia.** Está declarada en al menos 17 sistemas. Se comprueba en Odonthia (con aprobación) y Open Dental (Web Sched).
4. **Historia clínica con odontograma en los verticales dentales.** Se comprueba en Bilog, Dentalink, OdontoSoft, DentalBox y Dentidesk; en el resto está declarada. Los productos horizontales (AgendaPro, Turnito, SimpleTurno, Agendit) no lo evidencian.
5. **Caja, cobros y reportes básicos.** Son ofrecidos casi universalmente; se comprueban en Bilog, Dentalink, OdontoSoft y DentalBox.
6. **Modelo SaaS por suscripción mensual sin permanencia.** Es la norma: solo OdontoSoft Millennium, OdonticLabs y Open Dental mantienen instalación local o híbrida.

### C.2 Funcionalidades diferenciadoras reales (con evidencia)

| Diferencial | Sistema | Nivel de evidencia |
|---|---|---|
| Prevención de solapamientos por capacidad de sede (sillones), con sobreturno solo forzado tras alerta | Odonthia | C |
| Vistas de agenda por operatorio, bloqueos y superposición deshabilitada salvo configuración expresa | Open Dental | C |
| Lista ASAP con oferta de huecos liberados por enlace único | Open Dental | C |
| Reserva online del paciente que ingresa como pendiente y requiere confirmación del consultorio | Odonthia | C |
| Agenda por box y por profesional con bloqueo de turnos en el pasado | DentalBox | C |
| Firma remota con sello de tiempo, IP, dispositivo y hash SHA-256 | Odonthia | C |
| Periodontograma con índice de O'Leary y liquidación configurable de profesionales | OdontoSoft Millennium | C |
| Liquidación a obras sociales y profesionales | Bilog (C, como sección de ayuda); Dentalink (C, título de ayuda) | C parcial |
| Precio único publicado, todo incluido, con política de privacidad que cita la Ley 25.326 y la AAIP | DentalCore | C (precio y privacidad); funciones D |
| Validación de prácticas contra obras sociales y cierre multinivel hacia círculos | DentalTec | Solo D |
| Verificación de cobertura (PUCO), RENAPER, receta electrónica ReNaPDiS | ClinIA | Solo D |
| Capa de WhatsApp montada sobre sistemas existentes (Dentalink, Bilog, Benty) | Órbita | Solo D |
| Agentes de IA que agendan, reprograman y recuperan ausentes | Clinicorp, Órbita, Agendit, Doctocliq | Solo D |

**Juicio crítico.** La IA (dictado por voz, análisis de radiografías, agentes de WhatsApp) es el argumento comercial más repetido, pero **ningún** perfil la documenta con evidencia comprobada. Los diferenciales verificables son de **integridad de agenda** y **trazabilidad**, no de IA.

### C.3 Vacíos frecuentes del mercado argentino

1. **La prevención de solapamientos casi no se demuestra.** Solo Odonthia la comprueba; Open Dental lo hace de forma parcial. SimpleTurno ("detección de conflictos") y Agendit (vía Google Calendar) solo la declaran. En los otros 22 sistemas figura como "No evidenciado". La gestión por **sillón o box** está comprobada solo en Odonthia, Open Dental y DentalBox.
2. **La adecuación normativa argentina tiene escasa evidencia.** La Ley 25.326 solo aparece comprobada en Bilog, ClinIA, DentalCore y OdontoApp. La Ley 26.529 solo se comprueba en Odonthia (retención de 10 años); DentalCore la declara para su auditoría de accesos. La Ley 27.706 no está evidenciada en ningún sistema. Varios productos alojan datos fuera del país (Odonthia en Brasil; DentalCore posiblemente fuera de AR), y los extranjeros citan RGPD o LGPD, que no equivalen a la normativa argentina.
3. **Faltan auditoría y trazabilidad comprobadas.** Solo OdontoSoft Millennium tiene registros de auditoría comprobados. DentalTec, DentalBox y DentalCore los declaran, y Odonthia solo registra la firma remota.
4. **Hay opacidad de precios en el segmento local.** Bilog, ClinIA, Geblix, OdontoGRAMA y OdonticLabs no publican precios; OdontoApp tiene solo una cifra no verificada; DentalTec publica solo la mensajería. Entre los extranjeros con presencia en Argentina, Dentalink exige cotización. Varios publican en USD (DentalCore, Órbita, OdontoSoft, DentalBox), con exposición cambiaria.
5. **Las integraciones locales son solo declaradas.** ARCA/AFIP aparece en DentalTec, ClinIA y DentalCore; Mercado Pago, en DentalCore, SimpleTurno y Turnito (en AgendaPro con respaldo débil); la conexión con obras sociales, en DentalTec, ClinIA, Órbita y DentalCore. Ninguna está comprobada.
6. **La autogestión del paciente es incompleta.** La reprogramación autónoma y la lista de espera rara vez aparecen. Solo Open Dental comprueba la lista de espera (ASAP); DentalBox, Dental Office y Doctoralia la declaran.
7. **Los recordatorios por WhatsApp son caros o están limitados.** Hay cupos o cargos adicionales en AgendaPro (ARS 7.900 por 50 mensajes), DentalTec (USD 9 por 50), SimpleTurno (60/mes), Turnito (30/100), Simples Dental y Open Dental (texto por mensaje). En Odonthia el envío documentado es manual.

### C.4 Oportunidades de innovación

1. **Integridad de agenda demostrable.** Un motor que impida solapamientos por profesional **y** por sillón, con reglas visibles y mensajes de rechazo explicados, ataca el vacío C.3.1. Documentarlo públicamente sería en sí un diferencial frente a competidores que solo lo declaran.
2. **Trazabilidad del ciclo de vida del turno.** Registrar quién creó, confirmó, canceló o reprogramó cada turno y cuándo cubre el vacío de auditoría (C.3.3) a bajo costo y prepara la adecuación a las Leyes 25.326 y 26.529.
3. **Cumplimiento desde el diseño.** Datos mínimos del paciente, sin información clínica en el MVP, y una política de privacidad que cite expresamente la normativa argentina. Pocos competidores locales lo comprueban.
4. **Precio transparente en ARS con plan de entrada.** Odonthia, SimpleTurno y Turnito fijan la referencia de un plan gratuito; competir con precios opacos es una desventaja.
5. **Confirmación por enlace de WhatsApp sin API.** El enfoque de Odonthia (wa.me con texto precargado y enlace de confirmación) logra la funcionalidad más pedida del mercado sin costo de integración. Es una etapa intermedia razonable antes de la API oficial.
6. **Relleno de huecos.** Una lista de espera que ofrezca turnos liberados por cancelación (modelo ASAP de Open Dental) tiene casi ninguna implementación comprobada en la región.

---

## D. Recomendación final

### D.1 Cinco competidores prioritarios para analizar mediante demo

Las demostraciones **quedan fuera del alcance de esta fase**: no se contactó a ningún proveedor ni se crearon cuentas. La selección prioriza sistemas cuyas afirmaciones declaradas conviene verificar por su relevancia para el producto.

1. **Odonthia.** Es el competidor directo más cercano al MVP (consultorio argentino, agenda multiprofesional con sillones y prevención de solapamientos). Su plan gratuito permite una evaluación propia sin contacto comercial en una fase posterior. Convendría verificar si el recordatorio de WhatsApp de los planes pagos es realmente automático.
2. **Bilog.** Es el actor local de mayor escala declarada (más de 1.500 clínicas), con app nativa y liquidaciones a obras sociales. Habría que verificar el comportamiento de la agenda ante solapamientos y sillones, que no está evidenciado.
3. **Dentalink.** Es el referente regional con versión /ar/ y la ayuda pública más amplia. Habría que verificar su manejo de bloqueos y sillones y si cuenta con soporte local.
4. **DentalBox.** Tiene la agenda por box y profesional y la lista de espera más cercanas al modelo de sillones del MVP. Habría que verificar si previene solapamientos (hoy solo está comprobado que impide turnos en el pasado) y cómo opera en Argentina.
5. **Doctoralia.** Es el canal de captación de pacientes con reseñas verificadas (Capterra 4,7/415) y precios en ARS, y declara flujos de WhatsApp para confirmar, cancelar o reprogramar. Funciona como referencia de lo que el paciente argentino ya espera.

*Alternativas para una etapa posterior centrada en obras sociales y facturación:* DentalTec y ClinIA, cuyas integraciones locales son íntegramente declaradas.

### D.2 Tres productos de referencia para experiencia de usuario

1. **Odonthia.** Su documentación pública describe con precisión una columna y un color por profesional, las vistas día/semana/mes, el modo "Compacto" para móvil, la sala de espera con alerta visual a los 20 minutos, la confirmación por enlace y el flujo de reserva "pendiente, luego confirmado" (C).
2. **Open Dental.** Su manual público muestra vistas de agenda configurables por operatorio y profesional, bloqueos con clic derecho, el Pinboard para reubicar turnos y las listas de no agendados y ASAP (C). Es la mejor referencia para la interacción con varios sillones.
3. **DentalBox.** Sus páginas de función muestran la vista por box y por profesional, el arrastre de turnos entre horarios y boxes y el bloqueo de turnos en el pasado (C). Es una referencia directa para la vista de recepción.

### D.3 MVP sugerido

**Primer change.** El primer change se limita a **crear un turno sin solapamientos por profesional y por sillón**, como lógica de dominio pura y con tests automatizados por escenario. El resto de los imprescindibles se distribuye en changes posteriores; la interfaz web se construye sobre la lógica ya probada.

**Imprescindibles (núcleo de dominio):**
1. Agenda con vistas diaria y semanal, filtrable por profesional y por sillón.
2. Prevención de solapamientos por profesional **y** por sillón, validada en el dominio (no solo en la interfaz), con motivo de rechazo explícito.
3. Turnos dentro del horario laboral del profesional y fuera de bloqueos; sin turnos en el pasado.
4. Duración variable según la prestación.
5. Ciclo de vida del turno: dar, cancelar y reprogramar, con los estados reservado, confirmado, atendido, ausente y cancelado, y transiciones válidas explícitas.
6. Roles: odontólogo, secretaría/recepción y administrador/dueño.
7. Paciente con datos mínimos (nombre, DNI, teléfono, obra social como texto), sin información clínica.
8. **Historial de transiciones del turno** (quién, cuándo, de qué estado a cuál). Aceptado dentro del MVP; se implementa en el change del ciclo de vida del turno, no en el primer change.

**Diferenciadores del MVP:**
1. Mensajes de rechazo explicativos ante conflictos (qué turno o qué bloqueo genera el choque), como diferencial frente a un mercado que no demuestra esta validación. Acompañan a la validación de solapamientos desde el primer change.
2. Vista de recepción por sillón (referencia: DentalBox, Open Dental), en el change de interfaz.

**Para etapas posteriores:**
1. Búsqueda del primer hueco disponible que cumpla a la vez con profesional, sillón y duración de la prestación (inspirada en el Pinboard y la lista ASAP de Open Dental).
2. Confirmación y recordatorio por WhatsApp mediante enlace con texto precargado (sin API), y luego la API oficial.
3. Reserva online del paciente con aprobación del consultorio.
4. Lista de espera para cubrir cancelaciones.
5. Regla de no superposición de turnos del mismo paciente.
6. Sobreturnos controlados con alerta y autorización.
7. Señas y cobros (Mercado Pago), facturación ARCA y obras sociales (validación de cobertura).
8. Historia clínica y odontograma; multisede; reportes de ausentismo; exportación de datos.

**Comparación con las decisiones del usuario:**

| Tema | Decisión del usuario | Recomendación del analista | Relación |
|---|---|---|---|
| Solapamiento por profesional y por sillón | Incluido en el MVP | Incluido como núcleo; es el vacío más claro del mercado | Coincide |
| Solapamiento del mismo paciente | Diferido | Diferido, con el modelo preparado para añadirlo | Coincide |
| Sobreturnos | Prohibidos en el MVP | Prohibidos en el MVP. El mercado (Odonthia, Open Dental) los permite con alerta, por lo que conviene modelar la regla para habilitarlos luego | Coincide, con matiz de diseño |
| Duración variable, horario laboral, bloqueos, sin turnos en el pasado | Incluidos | Incluidos | Coincide |
| Estados y ciclo de vida | Cinco estados | Cinco estados con transiciones válidas explícitas | Coincide |
| Historial de transiciones del turno | Aceptado en el MVP, dentro del change del ciclo de vida (no en el primer change) | Incluido en el MVP por el vacío de trazabilidad del mercado (C.3.3) | Coincide |
| Alcance del primer change | Solo crear un turno sin solapamientos por profesional y por sillón | Núcleo de dominio validado antes de la interfaz | Coincide |
| Roles | Tres roles | Tres roles | Coincide |
| Datos del paciente | Mínimos, ficticios, sin datos clínicos | Mínimos, sin datos clínicos | Coincide |
| Integraciones externas | Ninguna en el MVP | Ninguna en el MVP; primera evolución: enlace de WhatsApp sin API | Coincide; se sugiere priorizar el enlace de WhatsApp en la etapa 2, dado que es la expectativa de mercado más extendida |
| Autogestión del paciente | Posterior al MVP | Posterior al MVP | Coincide |
| Búsqueda de primer hueco | Para etapas posteriores | Para etapas posteriores | Coincide |
| Diferenciadores del MVP | Mensajes de rechazo explicativos y vista de recepción por sillón (esta última en el change de interfaz) | Los mismos dos | Coincide |

---

## Verificación de fuentes

---

## Referencias

Fuentes citadas en las fichas de relevamiento (`docs/discovery/sources/`), agrupadas por sistema en el orden de la tabla A.1. Todas las consultas e intentos de consulta se realizaron el 2026-10-03. La columna "Estado" distingue las fuentes efectivamente consultadas de las que no fueron accesibles (error HTTP o de conexión), las que no se abrieron (solo se vieron en un buscador o enlazadas) y los fragmentos de buscador no verificables. Solo las fuentes consultadas sustentan evidencia en el informe.

### Odonthia

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial | https://odonthia.com/ | 2026-10-03 | Consultada |
| F2 | precios | https://odonthia.com/planes | 2026-10-03 | Consultada |
| F3 | oficial (funcionalidades) | https://odonthia.com/funcionalidades | 2026-10-03 | Consultada |
| F4 | oficial (seguridad) | https://odonthia.com/seguridad | 2026-10-03 | Consultada |
| F5 | ayuda (documentación: agenda y turnos) | https://odonthia.com/docs/agenda-y-turnos.md | 2026-10-03 | Consultada |
| F6 | ayuda (documentación: reserva online) | https://odonthia.com/docs/reserva-online.md | 2026-10-03 | Consultada |
| F7 | ayuda (índice de documentación) | https://odonthia.com/docs | 2026-10-03 | Consultada |

### Bilog

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial | https://bilog.com.ar/ | 2026-10-03 | Consultada |
| F2 | ayuda | https://docs.bilog.com.ar | 2026-10-03 | Consultada |
| F3 | precios (no accesible, 404) | https://bilog.com.ar/precios | 2026-10-03 | **No accesible** |
| F4 | oficial (términos y condiciones) | https://bilog.com.ar/terms_and_conditions | 2026-10-03 | Consultada |
| F5 | tienda (App Store) | https://apps.apple.com/ar/app/bilog-gesti%C3%B3n-odontol%C3%B3gica/id1554140449 | 2026-10-03 | Consultada |
| F6 | búsqueda web (fragmento, no verificable) | resultados de búsqueda sobre bilog.com.ar | 2026-10-03 | **Fragmento de buscador** (no verificable) |
| F7 | tienda (Google Play, no accesible) | https://play.google.com/store/apps/details?id=com.bilog.gomobile | 2026-10-03 | **No accesible** |

### DentalCore

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial | https://dentalcore.app/ | 2026-10-03 | Consultada |
| F2 | precios | https://dentalcore.app/pricing | 2026-10-03 | Consultada |
| F3 | ayuda (FAQ, respuestas no visibles) | https://dentalcore.app/faq | 2026-10-03 | Consultada |
| F4 | oficial (términos) | https://dentalcore.app/terms | 2026-10-03 | Consultada |
| F5 | oficial (acerca de) | https://dentalcore.app/about | 2026-10-03 | Consultada |
| F6 | oficial (privacidad) | https://dentalcore.app/privacy | 2026-10-03 | Consultada |

### ClinIA

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial | https://www.clinia.com.ar/odontologia | 2026-10-03 | Consultada |
| F2 | oficial (catálogo funcional PDF) | https://www.clinia.com.ar/catalogo-funcional.pdf | 2026-10-03 | Consultada |
| F3 | ayuda (FAQ) | https://www.clinia.com.ar/faq | 2026-10-03 | Consultada |
| F4 | oficial (seguridad) | https://www.clinia.com.ar/seguridad | 2026-10-03 | Consultada |
| F5 | oficial (privacidad y términos, enlazados; no inspeccionados) | https://www.clinia.com.ar/privacidad ; https://www.clinia.com.ar/terminos | 2026-10-03 | **No abierta** (solo vista en buscador o enlazada) |

### DentalTec

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial / precios de mensajería | https://web.dentaltec.com.ar/ | 2026-10-03 | Consultada |
| F2 | oficial (funcionalidades) | https://web.dentaltec.com.ar/funcionalidades | 2026-10-03 | Consultada |
| F3 | ayuda (preguntas frecuentes) | https://web.dentaltec.com.ar/preguntas-frecuentes | 2026-10-03 | Consultada |
| F4 | video (no inspeccionado) | https://www.youtube.com/playlist?list=PL4MN1RxFkCQqzCEsz2TGIlTROOwmLFdBG | 2026-10-03 | **No abierta** (solo vista en buscador o enlazada) |

### Órbita

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial | https://hiorbita.com/ | 2026-10-03 | Consultada |
| F2 | precios | https://hiorbita.com/precios | 2026-10-03 | Consultada |
| F3 | oficial (privacidad) | https://hiorbita.com/politica-de-privacidad | 2026-10-03 | **No accesible** |

### OdontoSoft Millennium

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial | https://gbsystems.com/os/ | 2026-10-03 | Consultada |
| F2 | ayuda (FAQ) | https://gbsystems.com/os/faqs.htm | 2026-10-03 | Consultada |
| F3 | oficial (producto) | https://gbsystems.com/os/producto.htm | 2026-10-03 | Consultada |
| F4 | oficial (resultado de búsqueda, mismo dominio) | https://gbsystems.com/os/suscripcion.htm | 2026-10-03 | **No abierta** (solo vista en buscador o enlazada) |
| F5 | oficial (módulo web) | https://gbsystems.com/os/web.htm | 2026-10-03 | Consultada |
| F6 | oficial (empresa) | https://gbsystems.com/os/acerca.htm | 2026-10-03 | Consultada |
| F7 | oficial (SMS) | https://gbsystems.com/os/sms.htm | 2026-10-03 | Consultada |
| F8 | precios | https://gbsystems.com/os/precios.htm | 2026-10-03 | Consultada |
| F9 | reseñas (búsqueda sin resultados verificables) | WebSearch "OdontoSoft Millennium GB Systems opiniones reseñas" | 2026-10-03 | **Fragmento de buscador** (no verificable) |

### OdontoApp

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial | https://odontoapp.com.ar/ | 2026-10-03 | Consultada |
| F2 | oficial (términos) | https://odontoapp.com.ar/terminos | 2026-10-03 | Consultada |
| F3 | oficial (privacidad) | https://odontoapp.com.ar/privacidad | 2026-10-03 | Consultada |
| F4 | búsqueda (resumen de terceros, no verificado) | https://odontoapp.com.ar/ vía WebSearch | 2026-10-03 | **Fragmento de buscador** (no verificable) |
| F5 | tienda | https://apps.apple.com/bo/app/odontoapp/id1462363537 | 2026-10-03 | **No accesible** |

### OdontoGRAMA

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial | https://odontograma.com.ar/ | 2026-10-03 | Consultada |
| F2 | oficial (empresa proveedora; no inspeccionada) | https://solsoftware.com.ar/ | 2026-10-03 | **No abierta** (solo vista en buscador o enlazada) |
| F3 | búsqueda web (fragmentos secundarios) | resultados de búsqueda "OdontoGRAMA Solsoftware" | 2026-10-03 | **Fragmento de buscador** (no verificable) |
| F4 | precios, ayuda, términos, privacidad, video, tiendas | no halladas / no accesibles | 2026-10-03 | **No accesible** |

### OdonticLabs

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial | http://islabs.com.ar/OdonticLabs/ | 2026-10-03 | Consultada |

### Geblix

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial | https://microfit.com.ar/software-de-gestion-odontologica/ | 2026-10-03 | Consultada |
| F2 | oficial | https://www.geblix.com/ | 2026-10-03 | Consultada |
| F3 | oficial (acceso de prueba enlazado desde F1; no accesible, HTTP 404) | https://www.geblix.com/inicio/referral | 2026-10-03 | **No accesible** |
| F4 | precios | https://microfit.com.ar/ (sin precios en las páginas consultadas) | 2026-10-03 | Consultada parcialmente |

### SimpleTurno

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial / precios (rubro odontología) | https://simpleturno.com/rubros/odontologia | 2026-10-03 | Consultada |
| F2 | oficial (home, FAQ) | https://simpleturno.com/ | 2026-10-03 | Consultada |
| F3 | oficial (política de privacidad) | https://simpleturno.com/privacidad | 2026-10-03 | **No accesible** |
| F4 | oficial (comparativa del proveedor, material comercial) | https://simpleturno.com/comparar/simpleturno-vs-turnito | 2026-10-03 | Consultada |
| F5 | oficial (empresa proveedora) | https://5studios.dev/ | 2026-10-03 | **No abierta** (solo vista en buscador o enlazada) |

### Turnito

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial / precios | https://turnito.app/ | 2026-10-03 | Consultada |
| F2 | oficial (versión Argentina, FAQ y precios) | https://turnito.app/ar/ | 2026-10-03 | Consultada |
| F3 | oficial (rubro médico) | https://turnito.app/ar/app-turnos-medicos/ | 2026-10-03 | Consultada |
| F4 | resultado de búsqueda (reseñas Google declaradas por el sitio) | WebSearch "Turnito app Argentina reseñas" | 2026-10-03 | **Fragmento de buscador** (no verificable) |
| F5 | oficial (página de precios) | https://turnito.app/precios | 2026-10-03 | **No accesible** |

### Dentalink

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial | https://www.softwaredentalink.com/ar/ | 2026-10-03 | Consultada |
| F2 | precios | https://www.softwaredentalink.com/ar/planes | 2026-10-03 | Consultada |
| F3 | ayuda | https://ayuda.softwaredentalink.com/es/collections/9620066-conoce-todos-los-modulos-de-dentalink | 2026-10-03 | Consultada |
| F4 | oficial | https://www.softwaredentalink.com/ar/experiencia-de-pacientes/odontograma-y-periodontograma | 2026-10-03 | Consultada |
| F5 | oficial (resultado de búsqueda, no abierto) | https://www.softwaredentalink.com/experiencia-de-pacientes/agenda | 2026-10-03 | **No abierta** (solo vista en buscador o enlazada) |
| F6 | oficial (blog, resumen de búsqueda) | https://www.softwaredentalink.com/blog/recordatorios-citas-whatsapp | 2026-10-03 | **Fragmento de buscador** (no verificable) |
| F7 | oficial | https://www.softwaredentalink.com/ar/soporte | 2026-10-03 | Consultada |
| F8 | oficial (misma página que F1) | https://www.softwaredentalink.com/ar/ | 2026-10-03 | Consultada |
| F9 | oficial de tercero (Órbita) | https://hiorbita.com/ | 2026-10-03 | Consultada |
| F10 | reseñas | https://www.capterra.com/p/196361/Dentalink/ (vía resultado de búsqueda; página no abierta) | 2026-10-03 | **No abierta** (solo vista en buscador o enlazada) |

### AgendaPro

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial | https://agendapro.com/ar/dental/software-odontologico | 2026-10-03 | Consultada |
| F2 | precios | https://agendapro.com/ar/planes | 2026-10-03 | Consultada |
| F3 | oficial | https://agendapro.com/ar/precios (devolvió 404 en un intento; el contenido citado proviene de la página oficial de software médico) https://agendapro.com/ar/centro-medico/software-para-centro-medico | 2026-10-03 | **No accesible** |
| F4 | oficial (blog; resultado de búsqueda, no abierto) | https://agendapro.com/blog/recordatorios-automaticos-de-agendapro/ | 2026-10-03 | **No abierta** (solo vista en buscador o enlazada) |
| F5 | oficial (resultado de búsqueda, no abierto) | https://agendapro.com/ar/centro-medico/software-para-centro-medico | 2026-10-03 | **No abierta** (solo vista en buscador o enlazada) |
| F6 | prensa (origen) | https://www.ex-ante.cl/negocios/agendapro-firma-chilena-gestiona-reservas/ | 2026-10-03 | Consultada |
| F7 | prensa (origen) | https://www.t13.cl/noticia/emprendedores/agendapro-startup-chilena-busca-impulsar-negocios-bienestar-y-salud | 2026-10-03 | Consultada |
| F8 | ayuda | http://ayuda.agendapro.com/es/ (solo categorías; artículos no leídos) | 2026-10-03 | Consultada parcialmente |
| F9 | tienda | https://play.google.com/store/apps/details?id=com.ionicframework.agendaproappiframe903400&hl=en_US | 2026-10-03 | Consultada |
| F10 | tienda | https://apps.apple.com/mx/app/agendapro-business/id1218956898 | 2026-10-03 | Consultada |

### Doctoralia (Pro / Clinic Cloud)

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial | https://www.doctoralia.com.ar/ | 2026-10-03 | **No accesible** |
| F1b | oficial | https://pro.doctoralia.com.ar/ | 2026-10-03 | **No accesible** |
| F2 | precios (Doctoralia Pro Argentina) | https://pro.doctoralia.com/ar/precio | 2026-10-03 | Consultada |
| F3 | oficial (agenda online, WhatsApp, lista de espera) | https://pro.doctoralia.com/ar/video-consulta-en-linea-1 (redirige desde academy.doctoraliar.com) | 2026-10-03 | Consultada |
| F4 | reseñas (Capterra) | https://www.capterra.com/p/253301/Doctoralia-Pro/ | 2026-10-03 | Consultada |
| F5 | oficial (Clinic Cloud) | https://clinic-cloud.com/ | 2026-10-03 | Consultada |
| F6 | reseñas (GetApp) | https://www.getapp.com/customer-management-software/a/doctoralia-pro/ | 2026-10-03 | Consultada |
| F7 | precios (Clinic Cloud) | https://clinic-cloud.com/tarifas | 2026-10-03 | Consultada |
| F8 | tienda App Store / Google Play, YouTube oficial | No consultados | 2026-10-03 | **No abierta** (solo vista en buscador o enlazada) |

### DentalBox

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial | https://www.dentalbox.app/ | 2026-10-03 | Consultada |
| F2 | precios | https://www.dentalbox.app/precios | 2026-10-03 | Consultada |
| F3 | oficial (función agenda) | https://www.dentalbox.app/funciones/agenda | 2026-10-03 | Consultada |
| F4 | oficial (función recordatorios) | https://www.dentalbox.app/funciones/recordatorios | 2026-10-03 | Consultada |
| F5 | oficial (resumen de búsqueda sobre el sitio) | https://www.dentalbox.app/ (resultado de WebSearch con extractos de funciones) | 2026-10-03 | **Fragmento de buscador** (no verificable) |
| F6 | oficial (función odontograma) | https://www.dentalbox.app/funciones/odontograma | 2026-10-03 | Consultada |
| F7 | oficial, no concluyente (pantalla de inicio de sesión, sin contenido) | https://www.dentalbox.app/argentina | 2026-10-03 | Consultada parcialmente |
| F8 | tienda | https://play.google.com/store/apps/details?id=com.applabsoftware.dentalbox&hl=en_US (no accesible vía WebFetch; solo extracto de resultado de búsqueda) | 2026-10-03 | **No accesible** |
| F9 | oficial | https://www.dentalbox.app/ (datos de empresa) | 2026-10-03 | Consultada |
| F10 | oficial (función pagos) | https://www.dentalbox.app/funciones/pagos | 2026-10-03 | Consultada |
| F11 | oficial (seguridad) | https://www.dentalbox.app/seguridad | 2026-10-03 | Consultada |
| F12 | reseñas (Capterra, listado general; sin ficha de DentalBox) | https://www.capterra.com/dental-software/ | 2026-10-03 | Consultada |

### Doctocliq

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial | https://www.doctocliq.com/ | 2026-10-03 | Consultada |
| F2 | precios | https://www.doctocliq.com/planes-y-precios | 2026-10-03 | Consultada |
| F3 | oficial (artículo del propio proveedor, contenido comercial) | https://www.doctocliq.com/mejor-software-dental | 2026-10-03 | Consultada |
| F4 | oficial (resultado de búsqueda, extracto) | https://www.doctocliq.com/software-dental-gratis-doctocliq | 2026-10-03 | **Fragmento de buscador** (no verificable) |
| F5 | oficial, no accesible (404) | https://www.doctocliq.com/precios | 2026-10-03 | **No accesible** |

### Dentidesk

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial | https://www.dentidesk.com | 2026-10-03 | Consultada |
| F2 | oficial (funcionalidades) | https://www.dentidesk.com/dentidesk/feature | 2026-10-03 | Consultada |
| F3 | oficial (soluciones) | https://www.dentidesk.com/dentidesk/solution | 2026-10-03 | Consultada |
| F4 | oficial (artículo de novedades) | https://www.dentidesk.com/dentidesk/detail/48 | 2026-10-03 | Consultada |
| F5 | tienda | https://apps.apple.com/cl/app/dentidesk-app/id6741155287 | 2026-10-03 | Consultada |
| F6 | reseñas / listado | https://www.capterra.com/p/184029/DENTIDESK/ | 2026-10-03 | Consultada |
| F7 | oficial, no accesible (404) | https://www.dentidesk.com/precios | 2026-10-03 | **No accesible** |
| F8 | oficial, no consultado (video) | https://www.youtube.com/@dentideskcanaloficialsoftw2220 | 2026-10-03 | **No abierta** (solo vista en buscador o enlazada) |

### Clinicorp

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial | https://www.clinicorp.com/ | 2026-10-03 | Consultada |
| F2 | precios | https://www.clinicorp.com/planos | 2026-10-03 | Consultada |
| F3 | oficial | https://www.clinicorp.com/agentes-clinicorp-ia | 2026-10-03 | Consultada |
| F4 | oficial | https://www.clinicorp.com/gestao-financeira-clinipay | 2026-10-03 | Consultada |
| F5 | reseñas | https://www.reclameaqui.com.br/empresa/clinicorp/ | 2026-10-03 | Consultada |

### Simples Dental

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial | https://www.simplesdental.com/ | 2026-10-03 | Consultada |
| F2 | precios | https://www.simplesdental.com/planos-e-precos | 2026-10-03 | Consultada |
| F3 | tienda (Google Play; solo extracto de búsqueda) | https://play.google.com/store/apps/details?id=com.simplesdental&hl=en_US | 2026-10-03 | **Fragmento de buscador** (no verificable) |
| F4 | tienda (App Store) | https://apps.apple.com/app/id954861717 | 2026-10-03 | Consultada |
| F5 | reseñas | https://www.capterra.com/p/219187/Simples-Dental/ | 2026-10-03 | Consultada |
| F6 | reseñas | https://www.getapp.com/healthcare-pharmaceuticals-software/a/simples-dental/ | 2026-10-03 | Consultada |
| F7 | oficial (política de privacidad; contenido detallado no accesible) | https://www.simplesdental.com/politica | 2026-10-03 | Consultada parcialmente |
| F8 | oficial, no accesible (404) | https://www.simplesdental.com/planos | 2026-10-03 | **No accesible** |

### Dental Office

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial/precios | https://www.dentaloffice.com.br/ | 2026-10-03 | Consultada |
| F2 | oficial | https://www.dentaloffice.com.br/agenda-para-dentistas/ | 2026-10-03 | Consultada |
| F3 | oficial | https://www.dentaloffice.com.br/funcionalidades/ | 2026-10-03 | Consultada |
| F4 | oficial (páginas /planos/ y /prontuario/) | https://www.dentaloffice.com.br/planos/ | 2026-10-03 | **No abierta** (solo vista en buscador o enlazada) |
| F5 | reseñas | https://www.reclameaqui.com.br/empresa/dental-office/ | 2026-10-03 | Consultada |
| F6 | reseñas (Google, vía resumen de búsqueda) | resumen de WebSearch; sin URL directa | 2026-10-03 | **Fragmento de buscador** (no verificable) |
| F7 | tienda | https://apps.apple.com/br/app/dental-office/id1567047922 | 2026-10-03 | **No accesible** |

### Agendit

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial y precios (misma página) | https://agendit.com.py/ | 2026-10-03 | Consultada |
| F2 | precios, no accesible (404) | https://agendit.com.py/planes | 2026-10-03 | **No accesible** |

### Open Dental

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial | https://www.opendental.com/ | 2026-10-03 | Consultada |
| F2 | ayuda (manual) | https://www.opendental.com/manual/appointments.html | 2026-10-03 | Consultada |
| F3 | oficial | https://www.opendental.com/site/websched.html | 2026-10-03 | Consultada |
| F4 | ayuda (manual) | https://www.opendental.com/manual/asaplist.html | 2026-10-03 | Consultada |
| F5 | precios | https://www.opendental.com/site/fees.html | 2026-10-03 | Consultada |
| F6 | precios | https://www.opendental.com/site/order.html | 2026-10-03 | Consultada |
| F7 | ayuda (manual, seguridad) | https://www.opendental.com/manual/securityadmin.html | 2026-10-03 | **No accesible** |
| F8 | reseñas | https://www.capterra.com/p/122350/Open-Dental/reviews/ | 2026-10-03 | **Fragmento de buscador** (no verificable) |
| F9 | ayuda (manual, Web Sched) | https://www.opendental.com/manual/websched.html | 2026-10-03 | **No accesible** |

### Dentrix

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial | https://www.dentrix.com/ | 2026-10-03 | Consultada |
| F2 | oficial | https://www.dentrix.com/dental-solutions/ | 2026-10-03 | Consultada |
| F3 | oficial | https://www.dentrix.com/dental-solutions/marketing-and-patient-experience/ | 2026-10-03 | Consultada |
| F4 | oficial | https://www.dentrix.com/dental-solutions/dentrix-connected-care-essentials/ | 2026-10-03 | Consultada |
| F5 | reseñas | https://www.capterra.com/p/2329/Dentrix/reviews/ | 2026-10-03 | **Fragmento de buscador** (no verificable) |

### Odontonet

| Ref. | Tipo | URL | Fecha | Estado |
|---|---|---|---|---|
| F1 | oficial | https://www.odontonet.es/ | 2026-10-03 | Consultada |
| F2 | precios | https://www.odontonet.es/precios/ | 2026-10-03 | Consultada |
| F3 | oficial | https://www.odontonet.es/modulos/ | 2026-10-03 | Consultada |
| F4 | reseñas | https://www.capterra.com/p/10012758/Odontonet/ | 2026-10-03 | **Fragmento de buscador** (no verificable) |
| F5 | reseñas (directorio) | https://www.capterra.es/directory/20027/dental/deployment-options/mac/software | 2026-10-03 | **Fragmento de buscador** (no verificable) |
| F6 | reseñas (blog de terceros) | https://www.akeito.com/blog/odontonet-opiniones/ | 2026-10-03 | **Fragmento de buscador** (no verificable) |
| F7 | oficial | https://www.odontonet.es/modulos/portal-del-paciente/ | 2026-10-03 | **No accesible** |
