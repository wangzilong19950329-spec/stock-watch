# syntax=docker/dockerfile:1.7
FROM node:22-alpine AS frontend-build
WORKDIR /workspace/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY frontend/ ./
RUN npm run build

FROM maven:3.9.9-eclipse-temurin-11 AS backend-build
WORKDIR /workspace
COPY pom.xml ./
COPY src/ ./src/
COPY --from=frontend-build /workspace/frontend/dist/ ./src/main/resources/static/
RUN --mount=type=cache,target=/root/.m2 mvn -B -Dmaven.test.skip=true package

FROM eclipse-temurin:11-jre-jammy
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=backend-build /workspace/target/stock-watch-1.0.0-SNAPSHOT.jar /app/stock-watch.jar
RUN mkdir -p /app/data
EXPOSE 8117
VOLUME ["/app/data"]
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=8 \
  CMD curl --fail --silent --show-error http://127.0.0.1:8117/ >/dev/null || exit 1
ENTRYPOINT ["java", "-jar", "/app/stock-watch.jar"]
