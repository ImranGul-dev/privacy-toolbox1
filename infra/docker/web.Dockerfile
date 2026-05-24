FROM node:22-alpine AS deps
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@9.15.4 --activate
COPY apps/web/package.json ./package.json
COPY apps/web/tsconfig.json apps/web/tailwind.config.ts apps/web/postcss.config.mjs apps/web/next.config.mjs ./
# No pnpm-lock.yaml is shipped in this ZIP yet, so install deterministically from package.json.
# After generating pnpm-lock.yaml locally, switch this to: pnpm install --frozen-lockfile
RUN pnpm install --frozen-lockfile=false

FROM node:22-alpine AS builder
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@9.15.4 --activate
COPY --from=deps /app/node_modules ./node_modules
COPY apps/web ./
ARG NEXT_PUBLIC_API_BASE_URL
ARG NEXT_PUBLIC_SITE_URL
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}
ENV NEXT_PUBLIC_SITE_URL=${NEXT_PUBLIC_SITE_URL}
RUN pnpm build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system nextjs && adduser --system --ingroup nextjs nextjs
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
