FROM python:3.12-alpine3.23@sha256:a4ad86fc2eaa4f9a5c3153776c9fb56e502dbd8e23dfa855d164308f376a6dd2 AS base

RUN apk upgrade --no-cache

FROM base AS dependencies

WORKDIR /build
COPY requirements.lock .
RUN python -m pip install --no-cache-dir --upgrade pip==26.3 \
    && python -m pip install --no-cache-dir --target /opt/dependencies -r requirements.lock

FROM base AS runtime

WORKDIR /code

RUN addgroup -S -g 10001 app \
    && adduser -S -D -H -u 10001 -G app app \
    && mkdir -p /data \
    && chown 10001:10001 /data \
    && python -m pip uninstall --yes pip setuptools \
    && python -c "import ensurepip,shutil; shutil.rmtree(ensurepip.__path__[0])"

COPY --from=dependencies /opt/dependencies /opt/dependencies
COPY app ./app

ENV DB_PATH=/data/cafeteria.db \
    PYTHONPATH=/opt/dependencies \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER 10001:10001
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
