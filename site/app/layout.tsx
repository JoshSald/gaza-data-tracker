import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Gaza Data Tracker",
  description:
    "Casualty, aid and food-security figures for Gaza, each linked to the body that published it and labelled as a count, a claim or an estimate.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Sans+Arabic:wght@400&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap"
        />
      </head>
      <body>
        <header className="site-head">
          <div className="wrap site-head-inner">
            <Link href="/" className="wordmark">
              Gaza Data Tracker
            </Link>
            <nav aria-label="Main">
              <Link href="/">Overview</Link>
              <Link href="/named-victims/">Named victims</Link>
              <Link href="/sources/">Sources</Link>
              <Link href="/methodology/">Method</Link>
            </nav>
          </div>
        </header>
        <main className="wrap">{children}</main>
        <footer className="site-foot">
          <div className="wrap">
            <p>
              Every figure links to the document it came from. Download the full dataset on the{" "}
              <Link href="/sources/">sources page</Link>.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
