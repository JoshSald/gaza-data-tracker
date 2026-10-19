"use client";
// Tabs whose selected tab follows the URL hash (#gaza, #oct7), so each list can be linked to directly.
import { useEffect, useState } from "react";
import { Tabs } from "@/components/ui/tabs";

export function HashTabs({ values, children, className }: { values: string[]; children: React.ReactNode; className?: string }) {
  const [value, setValue] = useState(values[0]);
  useEffect(() => {
    const read = () => {
      const h = window.location.hash.slice(1);
      if (values.includes(h)) setValue(h);
    };
    read();
    window.addEventListener("hashchange", read);
    return () => window.removeEventListener("hashchange", read);
  }, [values]);
  return (
    <Tabs
      value={value}
      onValueChange={(v) => {
        setValue(v);
        history.replaceState(null, "", `#${v}`);
      }}
      className={className}
    >
      {children}
    </Tabs>
  );
}
