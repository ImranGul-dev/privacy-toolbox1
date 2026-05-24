FROM python:3.12-slim-trixie

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=120 \
    DEBIAN_FRONTEND=noninteractive

ARG C2PATOOL_VERSION=0.26.59
ARG C2PATOOL_SHA256=
# c2patool official Linux binaries currently require a newer glibc than Debian Bookworm.
# The trixie base image provides a compatible libc, while keeping this image slim.

RUN set -eux; \
    printf 'Acquire::Retries "5";\nAcquire::http::Timeout "60";\nAcquire::https::Timeout "60";\n' > /etc/apt/apt.conf.d/80-retries; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      tar \
      libimage-exiftool-perl \
      qpdf \
      ghostscript \
      ffmpeg \
      libreoffice-writer \
      libreoffice-calc \
      libreoffice-impress \
      poppler-utils; \
    curl -fsSL -o /tmp/c2patool.tar.gz "https://github.com/contentauth/c2pa-rs/releases/download/c2patool-v${C2PATOOL_VERSION}/c2patool-v${C2PATOOL_VERSION}-x86_64-unknown-linux-gnu.tar.gz"; \
    if [ -n "$C2PATOOL_SHA256" ]; then echo "$C2PATOOL_SHA256  /tmp/c2patool.tar.gz" | sha256sum -c -; fi; \
    mkdir -p /tmp/c2patool; \
    tar -xzf /tmp/c2patool.tar.gz -C /tmp/c2patool; \
    find /tmp/c2patool -type f -name c2patool -exec install -m 0755 {} /usr/local/bin/c2patool \; ; \
    c2patool --version; \
    rm -rf /tmp/c2patool /tmp/c2patool.tar.gz /var/lib/apt/lists/*

WORKDIR /app
COPY apps/api/requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --retries 8 --timeout 120 -r requirements.txt
COPY apps/api /app
RUN addgroup --system app && adduser --system --ingroup app app && mkdir -p /data/privacy-toolbox && chown -R app:app /app /data/privacy-toolbox
USER app
ENV PYTHONPATH=/app
CMD ["celery","-A","app.workers.celery_app.celery_app","worker","--loglevel=INFO"]
