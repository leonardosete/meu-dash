# ---- Base Stage ----
FROM python:3.11-slim AS base

# create a non-root user
RUN groupadd -r nonroot && useradd -r -g nonroot -d /home/nonroot nonroot
RUN mkdir /home/nonroot && chown nonroot:nonroot /home/nonroot
ENV HOME=/home/nonroot

USER nonroot

# set work directory
WORKDIR /app

# install dependencies
COPY --chown=nonroot:nonroot requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---- App Stage ----
FROM python:3.11-slim AS app

# set work directory
WORKDIR /app

# create a non-root user
RUN groupadd -r nonroot && useradd -r -g nonroot nonroot

# create and chown directories
RUN mkdir -p /app/data/uploads && chown -R nonroot:nonroot /app/data
RUN mkdir -p /app/reports && chown -R nonroot:nonroot /app/reports

USER nonroot

# copy installed dependencies from base stage
COPY --from=base /home/nonroot/.local /home/nonroot/.local

# copy application code
COPY --chown=nonroot:nonroot src/ src/
COPY --chown=nonroot:nonroot templates/ templates/
COPY --chown=nonroot:nonroot migrations/ migrations/

# expose the port the app runs on
EXPOSE 5000

# run the application
CMD ["/bin/sh", "-c", "python -c 'from src.app import app, db; app.app_context().push(); db.create_all()' && /home/nonroot/.local/bin/gunicorn --bind 0.0.0.0:5000 src.app:app"]