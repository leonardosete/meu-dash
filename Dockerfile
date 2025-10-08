FROM python:3.13.8-alpine

# Instale só dependências básicas, minimizando CVEs do OS
RUN apk update && \
    apk upgrade --available && \
    apk add --no-cache \
        libffi-dev \
        musl-dev \
        tzdata && \
    rm -rf /var/cache/apk/*

RUN addgroup -S nonroot && adduser -S nonroot -G nonroot
USER nonroot
WORKDIR /app

COPY --chown=nonroot:nonroot requirements.txt .
RUN pip3 install --no-cache-dir --user -r requirements.txt

COPY --chown=nonroot:nonroot src/ src/
COPY --chown=nonroot:nonroot templates/ templates/
COPY --chown=nonroot:nonroot docs/ /app/docs/

EXPOSE 5000

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["/bin/sh", "-c", "gunicorn --bind 0.0.0.0:5000 src.app:app"]
