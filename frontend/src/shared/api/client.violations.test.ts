import { describe, expect, it } from "vitest";
import { createApiClient } from "./client";

describe("asViolations con campos opcionales", () => {
  it("captura conflictingAppointmentId, conflictingBlockId, conflictingInterval y referenceKind", async () => {
    const fetchFn = async () =>
      new Response(
        JSON.stringify({
          violations: [
            {
              code: "PROFESSIONAL_OVERLAP",
              message: "Solapamiento con Dra. Laura Quiroga",
              conflictingAppointmentId: "00000000-0000-0000-0000-0000000000a1",
              conflictingBlockId: "00000000-0000-0000-0000-0000000000e1",
              conflictingInterval: {
                startAt: "2026-11-16T13:00:00Z",
                endAt: "2026-11-16T13:30:00Z",
              },
              referenceKind: "PATIENT",
            },
          ],
        }),
        {
          status: 409,
          headers: { "Content-Type": "application/json" },
        },
      );

    const client = createApiClient({ fetchFn });
    const result = await client.request("/appointments", { method: "POST", body: {} });

    expect(result.ok).toBe(false);
    if (!result.ok && result.error.kind === "conflict") {
      const v = result.error.violations[0];
      expect(v).toBeDefined();
      if (!v) {
        throw new Error("Violation not found");
      }
      expect(v.code).toBe("PROFESSIONAL_OVERLAP");
      expect(v.message).toBe("Solapamiento con Dra. Laura Quiroga");
      expect(v.conflictingAppointmentId).toBe("00000000-0000-0000-0000-0000000000a1");
      expect(v.conflictingBlockId).toBe("00000000-0000-0000-0000-0000000000e1");
      expect(v.conflictingInterval).toEqual({
        startAt: "2026-11-16T13:00:00Z",
        endAt: "2026-11-16T13:30:00Z",
      });
      expect(v.referenceKind).toBe("PATIENT");
    } else {
      expect.fail("Se esperaba un error de tipo conflict con violaciones");
    }
  });
});
