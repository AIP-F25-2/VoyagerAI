FROM node:20-alpine AS builder

WORKDIR /app

ENV NEXT_DISABLE_ESLINT_PLUGIN=1

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build


# Runtime stage
FROM node:20-alpine AS runner

WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app ./

EXPOSE 3000

CMD ["npm", "start"]
