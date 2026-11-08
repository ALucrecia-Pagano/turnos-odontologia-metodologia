export function safeInternalPath(candidate: unknown): string {
  if (typeof candidate !== "string" || candidate === "" || !candidate.startsWith("/")) {
    return "/";
  }
  if (candidate.startsWith("//")) {
    return "/";
  }
  if (candidate === "/login" || candidate.startsWith("/login?") || candidate.startsWith("/login/")) {
    return "/";
  }
  return candidate;
}
