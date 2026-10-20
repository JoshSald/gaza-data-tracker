"use client";
// The overview's chapters: a list beside the sections on wide screens, a bar that stays at the top on narrow ones.
// The chapter being read is highlighted as you scroll.
import { useEffect, useState } from "react";

export function Chapters({ items }: { items: { id: string; label: string }[] }) {
  const [active, setActive] = useState<string | null>(null);

  useEffect(() => {
    const sections = items.map((i) => document.getElementById(i.id)).filter((s): s is HTMLElement => s !== null);
    // A section counts as being read once its top passes the upper third of the screen.
    const pick = () => {
      const line = window.innerHeight / 3;
      let current: string | null = null;
      for (const s of sections) if (s.getBoundingClientRect().top <= line) current = s.id;
      setActive(current);
    };
    pick();
    window.addEventListener("scroll", pick, { passive: true });
    window.addEventListener("resize", pick);
    return () => {
      window.removeEventListener("scroll", pick);
      window.removeEventListener("resize", pick);
    };
  }, [items]);

  // On narrow screens the bar scrolls sideways; keep the current chapter in view.
  useEffect(() => {
    if (!active) return;
    const link = document.querySelector<HTMLElement>(`.chapters a[href="#${active}"]`);
    const list = link?.closest("ol");
    if (link && list && list.scrollWidth > list.clientWidth) {
      list.scrollTo({ left: link.offsetLeft - list.clientWidth / 2 + link.clientWidth / 2, behavior: "smooth" });
    }
  }, [active]);

  return (
    <nav className="chapters" aria-label="Chapters">
      <p className="chapters-title">Chapters</p>
      <ol>
        {items.map((i) => (
          <li key={i.id}>
            <a href={`#${i.id}`} aria-current={active === i.id ? "location" : undefined}>
              {i.label}
            </a>
          </li>
        ))}
      </ol>
      <a href="#top" className="chapters-top">
        Back to top
      </a>
    </nav>
  );
}
