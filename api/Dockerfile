FROM node:22-alpine AS ui-build

WORKDIR /build/ui

COPY ui/package.json ui/package-lock.json ./
RUN npm ci

COPY ui ./
RUN npm run build

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api ./api
COPY src ./src
COPY --from=ui-build /build/ui/dist ./ui/dist

EXPOSE 8000

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
