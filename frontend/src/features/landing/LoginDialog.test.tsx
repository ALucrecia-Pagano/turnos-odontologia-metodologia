import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ApiResult, CurrentUser } from "../../shared/api/types";
import { SESSION_EXPIRED_MESSAGE } from "../auth/AuthContext";
import { LoginDialog } from "./LoginDialog";

const onLogin = async (): Promise<ApiResult<CurrentUser>> => ({
  ok: false,
  status: 500,
  error: { kind: "unknown", status: 500, rawText: "" },
});

const noop = () => undefined;

describe("LoginDialog", () => {
  it("abre con el diálogo, el heading, el formulario y el botón para recorrer la clínica", () => {
    render(<LoginDialog open onClose={noop} onLogin={onLogin} />);

    expect(screen.getByRole("dialog")).toHaveAttribute("aria-labelledby", "login-heading");
    expect(screen.getByRole("heading", { name: "Turnos Odontología" })).toBeVisible();
    expect(screen.getByRole("form", { name: "Iniciar sesión" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Ver la clínica" })).toBeVisible();
  });

  it("cierra el diálogo con el botón Ver la clínica", () => {
    let closes = 0;
    render(
      <LoginDialog
        open
        onClose={() => {
          closes += 1;
        }}
        onLogin={onLogin}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Ver la clínica" }));
    expect(closes).toBe(1);
  });

  it("muestra el aviso de sesión vencida dentro del formulario", () => {
    render(<LoginDialog open onClose={noop} onLogin={onLogin} initialNotice={SESSION_EXPIRED_MESSAGE} />);

    expect(screen.getByRole("alert")).toHaveTextContent(SESSION_EXPIRED_MESSAGE);
  });

  it("enfoca Usuario al abrir", () => {
    render(<LoginDialog open onClose={noop} onLogin={onLogin} />);

    expect(screen.getByLabelText("Usuario")).toHaveFocus();
  });

  it("bloquea el overflow del body mientras está abierto y lo restaura al cerrar", () => {
    document.body.style.overflow = "";
    const { rerender } = render(<LoginDialog open onClose={noop} onLogin={onLogin} />);
    expect(document.body.style.overflow).toBe("hidden");

    rerender(<LoginDialog open={false} onClose={noop} onLogin={onLogin} />);
    expect(document.body.style.overflow).toBe("");
  });
});
