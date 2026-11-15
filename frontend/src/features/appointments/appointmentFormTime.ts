export function buildStartAtIso(
  dateStr: string,
  timeStr: string,
  timeZone: string,
): string {
  const partsDate = dateStr.split("-").map(Number);
  const partsTime = timeStr.split(":").map(Number);
  const year = partsDate[0] ?? 2026;
  const month = partsDate[1] ?? 1;
  const day = partsDate[2] ?? 1;
  const hours = partsTime[0] ?? 0;
  const minutes = partsTime[1] ?? 0;
  const probeDate = new Date(Date.UTC(year, month - 1, day, hours, minutes));

  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    timeZoneName: "longOffset",
  }).formatToParts(probeDate);
  const rawOffset = parts.find((p) => p.type === "timeZoneName")?.value ?? "GMT";
  const offset = rawOffset.replace("GMT", "") || "+00:00";

  return `${dateStr}T${timeStr}:00${offset}`;
}
