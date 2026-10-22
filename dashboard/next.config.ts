import type { NextConfig } from "next";

// NEXT_OUTPUT=export builds plain files in out/ for a static host (Render Static Site: free and never asleep).
// Every page fetches from the API in the browser, so nothing needs a server. Without it, `npm run start` as always.
const staticExport = process.env.NEXT_OUTPUT === "export";

const nextConfig: NextConfig = staticExport
  ? { output: "export", trailingSlash: true } // /banco/ -> out/banco/index.html, which any static host serves
  : {};

export default nextConfig;
