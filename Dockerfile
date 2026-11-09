FROM python:3.13-slim

# mise runs the project tasks; uv is installed by mise per mise.toml
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://mise.run | MISE_INSTALL_PATH=/usr/local/bin/mise sh

ENV MISE_YES=1 \
    MISE_TRUSTED_CONFIG_PATHS=/app \
    PATH="/root/.local/share/mise/shims:${PATH}"

WORKDIR /app

COPY mise.toml pyproject.toml uv.lock ./
RUN mise install && mise run install

COPY . .

# render-engine's serve command hardcodes 127.0.0.1, which is unreachable from
# outside the container. Rebind it to 0.0.0.0 so Aiven Runtime can route traffic.
RUN sed -i 's/("127.0.0.1", port)/("0.0.0.0", port)/' \
    "$(mise exec -- uv run python -c 'import render_engine_cli.cli as c; print(c.__file__)')"

ENV SITE_URL=https://aivens-bot-blog.com

EXPOSE 8000

CMD ["mise", "run", "serve"]
