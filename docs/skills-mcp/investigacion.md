# Ficha de investigación: skill propia y MCP

**Proyecto:** sistema de turnos odontológicos · **Alumna:** Amanda Pagano · **Comisión:** 4 · **Agente principal:** Claude Code (Windows, Git Bash) · **Fecha:** 30/10/2026

## 1. Necesidad detectada

Los changes de interfaz tienen que cumplir lineamientos que hoy están repartidos en la base de conocimiento: estados de carga, vacío y error en toda vista; mensajes del dominio mostrados tal cual; permisos por rol; accesibilidad básica, y fechas y horas en hora local de Buenos Aires (KB 08 §Frontend cuidado, KB 07, KB 03 §RBAC, KB 04). Al preparar un change de UI es fácil olvidar alguno, y esa revisión se repite en cada change: conviene una **skill**. Además, el agente necesita **documentación actualizada del stack del front** (React 18, TypeScript, Vite) para no proponer APIs viejas o inventadas: eso lo resuelve un **MCP**.

## 2. Change elegido y alcance

**C-28 `ui-agenda-semanal`**: vista semanal por profesional, con los turnos en el día correcto en hora local y alternancia día/semana (US-040 CA-2).

**Dependencia:** C-28 depende de C-27 (agenda diaria), que todavía está pendiente, igual que la base del front y la API (C-25, C-26, C-22 a C-24). Por eso en este TP solo se **prepara** el change (explore, proposal, design, specs y tasks), sin implementarlo. La implementación queda para cuando el roadmap llegue a C-28, con sus dependencias terminadas. **Pendiente:** confirmar con el docente que esta elección es válida.

## 3. Skill creadora

`skill-creator`, de Anthropic: repositorio oficial `anthropics/skills`, carpeta `skills/skill-creator`, licencia Apache 2.0. Su proceso: capturar la intención, entrevistar, escribir el `SKILL.md` (con `name` y `description` en el frontmatter), armar casos de prueba, evaluar e iterar.

- **Instalación prevista** (a nivel proyecto, con copia versionada, como las demás skills del repo): `npx skills add anthropics/skills --skill skill-creator -a claude-code --copy`. El CLI `skills` requiere Node.js 22.20 o superior.
- **Comprobación:** que exista `.claude/skills/skill-creator/SKILL.md` y que el agente la reconozca en una sesión nueva.
- **Pendiente:** Active Stack ya instaló una `skill-creator` a nivel usuario (`~/.claude/skills/`, figura en `.atl/skill-registry.md`). Falta comparar si es igual a la oficial.

## 4. Skill propia: `appointment-frontend-ux`

| Campo | Definición |
|---|---|
| Propósito | Revisar la spec y las tareas de un change de UI de la agenda y detectar escenarios faltantes o reglas ambiguas antes de implementar. |
| Disparadores | Preparar o revisar un change de UI (C-25 a C-33); pedidos como "revisá los escenarios de la agenda" o "¿falta algún caso en esta pantalla?". |
| Entradas | Nombre del change; su delta spec y su `tasks.md`; KB 03, 04, 06, 07 y 08. |
| Procedimiento | 1) Leer los escenarios. 2) Recorrer un checklist: carga, vacío, error; cada código de violación que pueda devolver la API; rol sin permiso; teclado y foco; hora local (cambio de día, semana de 7 días). 3) Contrastar con la KB. 4) Listar los hallazgos. |
| Salida | Una tabla con el hallazgo, la sección de la KB que lo respalda y el escenario GIVEN/WHEN/THEN propuesto. No edita la spec sin aprobación. |
| Criterios de revisión | Cada hallazgo cita la KB; no inventa reglas de dominio; no propone validar reglas en el cliente (KB 08); los escenarios son verificables. |

**Un único `SKILL.md` portable.** El formato Agent Skills (carpeta con `SKILL.md`) es el mismo para los cinco agentes. La fuente canónica va en `.agents/skills/appointment-frontend-ux/SKILL.md` y se copia a `.claude/skills/` para Claude Code. El repo ya usa ese espejo, y en Windows se usa una copia porque los symlinks no son confiables. Después de cada edición se comprueba que las dos copias sean idénticas (`cmp`).

| Agente | Ruta de proyecto (según el CLI `skills`) | Comprobación prevista | Estado |
|---|---|---|---|
| Claude Code | `.claude/skills/` | Sesión nueva: pedirle que liste sus skills | PENDIENTE de prueba |
| Codex | `.agents/skills/` | Ídem | PENDIENTE de prueba |
| GitHub Copilot | `.agents/skills/` | Ídem | PENDIENTE de prueba |
| OpenCode | `.agents/skills/` | Ídem | PENDIENTE de prueba |
| Google Antigravity | `.agents/skills/` | Ídem | PENDIENTE de prueba |

## 5. Comparación de MCP

| Criterio | Context7 | Figma MCP |
|---|---|---|
| Autor | Upstash, `upstash/context7` (MIT) | Figma (servicio oficial) |
| Propósito | Documentación actualizada de librerías | Leer diseños de Figma y generar código o diseños |
| Herramientas | `resolve-library-id`, `query-docs` | Contexto de diseño, variables, capturas, escritura en el lienzo (nombres exactos: PENDIENTE) |
| Compatibilidad con Claude Code | Sí: servidor remoto o `npx ctx7 setup --claude` | Sí, figura como cliente soportado |
| Conexión | Remoto: `https://mcp.context7.com/mcp` | Remoto: `https://mcp.figma.com/mcp`; también hay uno de escritorio |
| Credenciales | API key gratuita, recomendada (da más límite de uso) | Cuenta de Figma con inicio de sesión; acceso a los archivos de diseño |
| Costos y límites | Plan gratuito con límites (detalle: PENDIENTE) | En el plan Starter, asientos View/Collab: 20 llamadas por mes. El servidor de escritorio requiere asiento Dev o Full en un plan pago |
| Datos que salen | Solo las consultas de documentación | Los diseños consultados |

**Elección: Context7.** Sirve para preparar C-28 ya, sin que exista el front. Por ejemplo, para consultar cómo mostrar fechas en una zona horaria con `Intl.DateTimeFormat` (el escenario "turno en el día correcto en hora local"), o la herramienta de tests de componentes que se elegirá en C-25 (SU-10). Figma no aporta en esta etapa: el proyecto no tiene diseños en Figma, y el plan gratuito permite muy pocas llamadas.

## 6. Instalación, configuración y verificación previstas (no ejecutadas)

1. Crear una API key gratuita en `context7.com/dashboard` y guardarla **solo** como variable de entorno `CONTEXT7_API_KEY`, nunca en el repo.
2. Registrar el servidor a nivel proyecto en `.mcp.json`, con la clave por expansión de variables (sintaxis `${VAR}` de Claude Code):
   `{"mcpServers": {"context7": {"type": "http", "url": "https://mcp.context7.com/mcp", "headers": {"Authorization": "Bearer ${CONTEXT7_API_KEY}"}}}}`
   No se usa `claude mcp add ... --header "Bearer $CONTEXT7_API_KEY"`, porque la terminal reemplazaría la variable por la clave y la clave quedaría escrita en el archivo.
3. **Verificar:** `claude mcp list` tiene que mostrar `✔ Connected`. Dentro de la sesión, `/mcp`. Claude Code pide aprobación la primera vez que usa un servidor de `.mcp.json`.
4. **Herramienta real:** `resolve-library-id` para "react" y `query-docs` sobre el formateo de fechas por zona horaria.

**Límites:** solo lectura de documentación pública; nunca se envían datos de pacientes ni código con secretos en las consultas.

## 7. Archivos de la fundación que se prevé actualizar

`.agents/skills/` y `.claude/skills/` (skill nueva) · `.atl/skill-registry.md` (registro) · `AGENTS.md` y `CLAUDE.md` (cuándo usar la skill y el MCP, idénticos entre sí) · `.mcp.json` (sin secretos) · `README.md` (requisitos, configuración y verificación del MCP) · `knowledge-base/09_decisiones_y_supuestos.md` (decisión del MCP) · `CHANGES.md` (referencia de C-28 preparado).

## 8. Fuentes (consultadas el 29 y el 30/10/2026)

- Consigna del TP, Metodología I (PDF de la cátedra).
- Anthropic, `skill-creator`: https://github.com/anthropics/skills/tree/main/skills/skill-creator
- skills.sh, ficha de la skill: https://www.skills.sh/anthropics/skills/skill-creator
- Vercel Labs, CLI `skills` y rutas por agente: https://github.com/vercel-labs/skills (`docs/agents.md`)
- Upstash, Context7: https://github.com/upstash/context7
- Anthropic, MCP en Claude Code: https://code.claude.com/docs/en/mcp
- Figma, guía del servidor MCP: https://help.figma.com/hc/en-us/articles/32132100833559
- Figma, límites y acceso: https://developers.figma.com/docs/figma-mcp-server/rate-limits-access/