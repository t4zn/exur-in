# -------------------------------------------------------------
# Stage 1: Build Next.js Static Export
# -------------------------------------------------------------
FROM node:22-alpine AS builder

WORKDIR /app

RUN npm install -g pnpm

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm build

# -------------------------------------------------------------
# Stage 2: Python FastAPI Runtime
# -------------------------------------------------------------
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy built frontend assets
COPY --from=builder /app/out ./out

# Copy python backend code
COPY backend/ ./backend/
COPY main.py .

# Copy environment template if exists
COPY .env* ./

EXPOSE 10000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
