# Evidencia 04 — Uso real del MCP Context7

Fecha: 2026-11-08
Repo: turnos-odontologia
Objetivo: usar el MCP `context7` de punta a punta (`resolve-library-id` + `query-docs`) para
preparar C-28, que va a llevar la semana en la URL con `useSearchParams`.

> Regla de seguridad respetada: la clave `CONTEXT7_API_KEY` no se escribe ni se imprime en ningún
> archivo, comando ni salida. La conexión usa la variable de entorno; no se muestra su valor.

---

## 1. `resolve-library-id`

**Herramienta:** `context7_resolve-library-id`

**Parámetros:**

| Parámetro | Valor |
|---|---|
| `libraryName` | `react-router` |
| `query` | `React Router useSearchParams hook in version 6` |

**Resultado (candidatos relevantes):**

| Título | Library ID | Versiones listadas | Reputación |
|---|---|---|---|
| React Router | `/remix-run/react-router` | 7.6.2, react-router@7.5.3, react_router_7_8_2, react-router_7.9.4, v5.2.1, v6.3.0 | High |
| React Router | `/websites/reactrouter` | **6.30.3**, v5, 7.13.0 | High |
| React Router (DeepWiki) | `/websites/deepwiki_remix-run_react-router` | — | High |

**ID elegido:** `/websites/reactrouter`, porque es el único candidato que indexa la serie **6.30**
(6.30.3), que es la que usa el repo (`react-router-dom@6.30.6`). El candidato principal
`/remix-run/react-router` está centrado en la 7 y solo lista `v6.3.0`.

## 2. `query-docs`

**Herramienta:** `context7_query-docs`

**Parámetros:**

| Parámetro | Valor |
|---|---|
| `libraryId` | `/websites/reactrouter` |
| `query` | `useSearchParams hook API in React Router v6: reading and setting URL search params, default values, setSearchParams callback form` |
| `language` | `TypeScript` |

**Resumen del resultado:**

- `useSearchParams(defaultInit?)` devuelve una tupla
  `[URLSearchParams, SetURLSearchParams]`.
- El segundo elemento, `setSearchParams`, **provoca una navegación** al actualizar la URL.
- Acepta: string (`"?tab=1"`), objeto (`{ tab: "1" }`), arrays para valores múltiples,
  array de tuplas y un `URLSearchParams`.
- También acepta una **función callback** (como el `setState` de React):
  `setSearchParams((searchParams) => { searchParams.set("tab", "2"); return searchParams; })`.
- Advertencia del callback: **no** soporta el encolado de React; varias llamadas en el mismo tick
  no se acumulan.
- `defaultInit` inicializa los params pero **no cambia la URL en el primer render**.
- `searchParams` es una referencia estable (sirve como dependencia de `useEffect`), pero es mutable:
  si se modifica sin llamar a `setSearchParams`, la URL no se actualiza.

**Fragmento corto (tal como lo devolvió el MCP):**

```tsx
let [searchParams, setSearchParams] = useSearchParams();

// a shorthand object
setSearchParams({ tab: "1" });

// a function callback like React's setState
setSearchParams((searchParams) => {
  searchParams.set("tab", "2");
  return searchParams;
});
```

## 3. Evaluación crítica

**¿La documentación corresponde a la versión 6.30 o a la 7?**

- El **índice** de la librería elegida sí incluye la serie 6.30 (6.30.3), y el repo usa
  `react-router-dom@6.30.6` (diferencia de parche, sin cambios de API).
- El **contenido** de la página, en cambio, es el de la documentación actual de
  `reactrouter.com`, que es la de la **v7**: el ejemplo importa desde `"react-router"`, no desde
  `"react-router-dom"`. En la v7 los paquetes se consolidaron; en la v6.30 este repo importa
  `useSearchParams` desde `react-router-dom` (que reexporta desde `react-router`).
- Conclusión: la **API del hook** (`useSearchParams`, `defaultInit`, formas de `setSearchParams`,
  callback) es la misma en v6 y v7, así que el resultado es utilizable para C-28, pero **hay que
  ajustar el import** a `react-router-dom` para la v6.30.6 del repo.

**¿Hubo algo incorrecto o desactualizado?**

- No se detectó nada **incorrecto** en la descripción del hook.
- Lo **desactualizado/ambiguo** es la ruta de import del ejemplo (estilo v7) y que la página no
  rotula explícitamente "v6". Además, el índice muestra 6.30.3 y no 6.30.6 (solo parche).
- Para C-28 la conclusión práctica es: usar `useSearchParams` desde `react-router-dom`, con la
  forma de objeto o el callback para actualizar la URL, sabiendo que cada `setSearchParams`
  navega y que el callback no encola como `setState`.
