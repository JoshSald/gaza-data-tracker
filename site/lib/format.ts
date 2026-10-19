// Number and date formatting, shared by server pages and client-side charts (no Node imports here).
export const fmt = (n: number) => new Intl.NumberFormat("en-GB").format(n);
export const fmtCompact = (n: number) =>
  new Intl.NumberFormat("en-GB", { notation: "compact", maximumFractionDigits: 1 }).format(n);

export function fmtDate(iso: string | null | undefined) {
  if (!iso) return "";
  const d = new Date(iso.slice(0, 10) + "T00:00:00Z");
  return new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" }).format(d);
}
