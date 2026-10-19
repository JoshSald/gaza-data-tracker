// Copies ../data into public/data so every published figure can also be downloaded as raw JSON.
import { cpSync, mkdirSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const from = join(here, "..", "..", "data");
const to = join(here, "..", "public", "data");
rmSync(to, { recursive: true, force: true });
mkdirSync(to, { recursive: true });
for (const name of ["sources.json", "metrics.json", "observations", "lists"]) {
  cpSync(join(from, name), join(to, name), { recursive: true });
}
console.log("Copied data/ to public/data/");
