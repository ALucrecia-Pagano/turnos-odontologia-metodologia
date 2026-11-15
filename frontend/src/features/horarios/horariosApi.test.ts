import { describe, expect, it } from "vitest";
import { createApiClient, type FetchFn } from "../../shared/api/client";
import {
  createBlock,
  deleteBlock,
  getWorkingHours,
  listBlocks,
  replaceWorkingHours,
} from "./horariosApi";

const PROF_ID = "00000000-0000-0000-0000-000000000001";
const BLOCK_ID = "00000000-0000-0000-0000-0000000000b1";

describe("horariosApi", () => {
  it("parsea respuestas exitosas de getWorkingHours, replaceWorkingHours, listBlocks, createBlock y deleteBlock", async () => {
    const calls: Array<{ url: string; method: string; body: string | null }> = [];
    const fetchFn: FetchFn = async (url, init) => {
      const method = init?.method ?? "GET";
      const body = typeof init?.body === "string" ? init.body : null;
      calls.push({ url, method, body });

      if (url.endsWith(`/professionals/${PROF_ID}/working-hours`) && method === "GET") {
        return new Response(
          JSON.stringify([{ weekday: 1, start: "09:00", end: "13:00" }]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith(`/professionals/${PROF_ID}/working-hours`) && method === "PUT") {
        return new Response(
          JSON.stringify({
            workingHours: [{ weekday: 1, start: "09:00", end: "14:00" }],
            appointmentsOutsideHours: [
              {
                id: "00000000-0000-0000-0000-0000000000a1",
                patientId: "00000000-0000-0000-0000-0000000000c1",
                patientName: "Lucía Gómez",
                chairId: "00000000-0000-0000-0000-0000000000d1",
                startAt: "2026-05-04T18:00:00Z",
                endAt: "2026-05-04T18:30:00Z",
                status: "confirmado",
              },
            ],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith(`/professionals/${PROF_ID}/blocks`) && method === "GET") {
        return new Response(
          JSON.stringify([
            {
              id: BLOCK_ID,
              professionalId: PROF_ID,
              startAt: "2026-05-06T12:00:00-03:00",
              endAt: "2026-05-06T15:00:00-03:00",
              reason: "Congreso",
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith(`/professionals/${PROF_ID}/blocks`) && method === "POST") {
        return new Response(
          JSON.stringify({
            block: {
              id: BLOCK_ID,
              professionalId: PROF_ID,
              startAt: "2026-05-06T12:00:00-03:00",
              endAt: "2026-05-06T15:00:00-03:00",
              reason: "Congreso",
            },
            affectedAppointments: [],
          }),
          { status: 201, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith(`/blocks/${BLOCK_ID}`) && method === "DELETE") {
        return new Response(
          JSON.stringify({
            id: BLOCK_ID,
            professionalId: PROF_ID,
            startAt: "2026-05-06T12:00:00-03:00",
            endAt: "2026-05-06T15:00:00-03:00",
            reason: "Congreso",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response("Not Found", { status: 404 });
    };

    const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn });

    const hoursRes = await getWorkingHours(client, PROF_ID);
    expect(hoursRes.ok).toBe(true);
    if (hoursRes.ok) {
      expect(hoursRes.data).toEqual([{ weekday: 1, start: "09:00", end: "13:00" }]);
    }

    const replaceRes = await replaceWorkingHours(client, PROF_ID, [
      { weekday: 1, start: "09:00", end: "14:00" },
    ]);
    expect(replaceRes.ok).toBe(true);
    if (replaceRes.ok) {
      expect(replaceRes.data.workingHours).toEqual([
        { weekday: 1, start: "09:00", end: "14:00" },
      ]);
      expect(replaceRes.data.appointmentsOutsideHours).toHaveLength(1);
      expect(replaceRes.data.appointmentsOutsideHours[0]?.patientName).toBe("Lucía Gómez");
    }

    const blocksRes = await listBlocks(client, PROF_ID);
    expect(blocksRes.ok).toBe(true);
    if (blocksRes.ok) {
      expect(blocksRes.data).toHaveLength(1);
      expect(blocksRes.data[0]?.reason).toBe("Congreso");
    }

    const createRes = await createBlock(client, PROF_ID, {
      startAt: "2026-05-06T12:00:00-03:00",
      endAt: "2026-05-06T15:00:00-03:00",
      reason: "Congreso",
    });
    expect(createRes.ok).toBe(true);
    if (createRes.ok) {
      expect(createRes.data.block.id).toBe(BLOCK_ID);
      expect(createRes.data.affectedAppointments).toEqual([]);
    }

    const deleteRes = await deleteBlock(client, BLOCK_ID);
    expect(deleteRes.ok).toBe(true);
    if (deleteRes.ok) {
      expect(deleteRes.data.id).toBe(BLOCK_ID);
    }

    expect(calls).toHaveLength(5);
    expect(calls[1]?.body).toBe(JSON.stringify([{ weekday: 1, start: "09:00", end: "14:00" }]));
  });
});
