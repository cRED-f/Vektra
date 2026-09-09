# ── Dockerfile for the Vektra Next.js frontend ────────────────────────
# Uses a MULTI-STAGE build. Why? Building the app needs the full Node toolchain
# (npm, TypeScript, devDependencies). Serving it does not. So we:
#   • STAGE 1 "builder": install everything, run `next build`
#   • STAGE 2 "runner": a fresh, tiny image that only copies the build output
# Result: the final image is small even though the build was heavy.

# ── Stage 1: builder ──────────────────────────────────────────────────
FROM node:24-alpine AS builder

WORKDIR /app

# Copy dependency manifests first (Docker caching — see backend notes).
COPY package.json package-lock.json ./

# npm ci installs EXACTLY what package-lock.json pins (vs npm install
# which may drift). CI = clean install.
RUN npm ci

# Copy the app source, then build.
COPY . .
RUN npm run build

# ── Stage 2: runner ───────────────────────────────────────────────────
# A fresh, minimal image — no npm, no dev tooling.
FROM node:24-alpine AS runner

WORKDIR /app

# The `next build` step wrote a self-contained folder to .next/standalone
# (because we set `output: "standalone"` in next.config.ts). Copy it in.
COPY --from=builder /app/.next/standalone ./

# Copy static assets so the standalone server can serve them too.
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# The standalone server reads these env vars for host/port.
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

EXPOSE 3000

CMD ["node", "server.js"]