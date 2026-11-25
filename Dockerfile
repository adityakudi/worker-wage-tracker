FROM node:22-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ENV VITE_API_BASE_URL=/api
RUN npm run build

FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt \
    && useradd --create-home --uid 10001 tracker
COPY backend/ ./backend/
COPY --from=frontend /build/dist ./frontend/dist
USER tracker
EXPOSE 8000
CMD ["python", "-m", "backend.serve"]
