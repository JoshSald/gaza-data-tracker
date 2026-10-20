// A section folded away under a one-line summary, so long explanations do not push the content below out of view.
import { cn } from "@/lib/utils";

export function Disclosure({ summary, children, className }: { summary: React.ReactNode; children: React.ReactNode; className?: string }) {
  return (
    <details className={cn("group text-sm [&_p]:my-3 [&_ul]:my-3", className)}>
      <summary className="cursor-pointer list-none font-medium marker:hidden [&::-webkit-details-marker]:hidden">
        <span className="mr-1.5 inline-block transition-transform group-open:rotate-90" aria-hidden>
          ▸
        </span>
        {summary}
      </summary>
      {children}
    </details>
  );
}
