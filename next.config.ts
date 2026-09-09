import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* Standalone output: emits .next/standalone with only the runtime files
     needed to serve the app — makes the Docker image tiny. */
  output: "standalone",
};

export default nextConfig;