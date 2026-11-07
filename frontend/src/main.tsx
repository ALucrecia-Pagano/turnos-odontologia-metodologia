import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./shared/styles/tokens.css";
import "./shared/styles/reset.css";

const container = document.getElementById("root");
if (container === null) {
  throw new Error("No se encontró el elemento #root.");
}

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
