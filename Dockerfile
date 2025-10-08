FROM alpine:latest

RUN apk update && \
    apk add --no-cache python3 py3-pip python3-dev \
        build-base \
        libffi-dev \
        musl-dev \
        openblas-dev \
        tzdata && \
    rm -rf /var/cache/apk/*

RUN addgroup -S nonroot && adduser -S nonroot -G nonroot
USER nonroot
WORKDIR /app

COPY --chown=nonroot:nonroot requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY --chown=nonroot:nonroot src/ src/
COPY --chown=nonroot:nonroot templates/ templates/
COPY --chown=nonroot:nonroot docs/ /app/docs/

EXPOSE 5000

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["/bin/sh", "-c", "gunicorn --bind 0.0.0.0:5000 src.app:app"]
