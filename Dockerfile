# ─────────── Base image ───────────
FROM python:3.11-slim

# ─────────── Install dependencies ───────────
WORKDIR /app
COPY app/requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# ─────────── Copy your code ───────────
COPY app/ .

# ─────────── Flask settings ───────────
ENV FLASK_APP=main
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8080

# ─────────── Expose port & launch ───────────
EXPOSE 8080
CMD ["flask", "run"]
