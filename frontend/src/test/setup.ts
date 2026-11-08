import { transferableAbortController } from "node:util";
import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// jsdom 31 define su propio AbortController/AbortSignal pero conserva Request de Node 24 (undici);
// React Router 6 crea un Request con AbortSignal en cada navegación (<Navigate /> / createMemoryRouter).
const sampleAbortController = transferableAbortController();
window.AbortController = sampleAbortController.constructor as typeof AbortController;
window.AbortSignal = sampleAbortController.signal.constructor as typeof AbortSignal;

afterEach(() => {
  cleanup();
});
