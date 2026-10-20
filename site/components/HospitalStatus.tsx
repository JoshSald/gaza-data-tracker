// A hospital's status as WHO last named it: the badge with WHO's wording, and a small dot beside the name.
// Kept apart from Figure.tsx, which reads data files, so the client-side hospital list can use it.
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export type HospitalStatus = "partially_functioning" | "not_functioning" | "destroyed" | "services_reported";

export const STATUS_LABEL: Record<HospitalStatus, string> = {
  partially_functioning: "Partially functioning",
  not_functioning: "Not functioning",
  destroyed: "Destroyed",
  services_reported: "Services reported",
};
const STATUS_STYLE: Record<HospitalStatus, string> = {
  partially_functioning: "border-transparent bg-[var(--status-partial)] text-white",
  not_functioning: "border-transparent bg-[var(--status-down)] text-white",
  destroyed: "border-transparent bg-[var(--red)] text-white",
  services_reported: "border-[var(--status-partial)] text-foreground",
};
export const NO_STATUS = "No recent named status from WHO";

export function HospitalStatusBadge({ status }: { status?: HospitalStatus }) {
  if (!status) return <span className="text-muted-foreground">{NO_STATUS}</span>;
  return (
    <Badge variant="outline" className={cn("h-auto rounded-[2px] px-[0.5em] py-[0.2em] text-xs font-medium whitespace-nowrap", STATUS_STYLE[status])}>
      {STATUS_LABEL[status]}
    </Badge>
  );
}

/** The dot beside a hospital's name. It pulses only for hospitals WHO last named as partially functioning, and not
 * at all for readers who ask their device for reduced motion. Its meaning is in the label, never in colour alone. */
export function HospitalStatusDot({ status }: { status?: HospitalStatus }) {
  const label = status ? STATUS_LABEL[status] : NO_STATUS;
  return (
    <span className={cn("status-dot", status ? `status-dot-${status}` : "status-dot-none")} role="img" aria-label={label} title={label} />
  );
}
