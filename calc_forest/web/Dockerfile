# =============================================================
#  我的计算森林 — Next.js 15.5 Frontend
# =============================================================
# 多阶段构建: builder → runner, 最小化镜像体积

# --- Stage 1: Install deps & build ---
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# standalone output 需要 next.config.ts 中 output: "export" 或 "standalone"
# 当前项目未配置 standalone, 使用完整 .next 构建
RUN npx next build --no-lint

# --- Stage 2: Production runner ---
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# 创建非 root 用户
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# 复制构建产物
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.ts ./next.config.ts

USER nextjs

EXPOSE 3000

# Next.js 15 默认 start 命令
CMD ["npm", "start", "--", "-p", "3000"]
