import type { NextConfig } from "next";

// A fully static site: every page is built from the files in ../data at build time.
const config: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
};

export default config;
