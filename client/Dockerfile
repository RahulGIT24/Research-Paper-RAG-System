FROM node:22-alpine AS deps

WORKDIR /app

# RUN npm install -g pnpm

COPY package.json  ./

# RUN pnpm approve-builds

RUN npm install

FROM node:22-alpine AS runner

WORKDIR /app

# RUN npm install -g pnpm

ARG NEXT_PUBLIC_API_URL

ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]