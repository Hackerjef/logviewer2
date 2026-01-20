FROM python:3.13.11-slim-bookworm as py
ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  OAUTHLIB_INSECURE_TRANSPORT=1
RUN apt update && apt full-upgrade -y && apt install -y curl gnupg2
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - && echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt update && apt install -y git bash yarn curl gcc build-essential yarn
RUN curl -sSL install.python-poetry.org | POETRY_HOME=/opt/poetry python -
ENV PATH /opt/poetry/bin:$PATH

FROM py

LABEL org.opencontainers.image.source=https://github.com/hackerjef/logviewer2
LABEL org.opencontainers.image.description="logviewer2: A web-based log viewer"
LABEL org.opencontainers.image.licenses=unlicense

WORKDIR /logviewer2
ENV ENV docker
COPY . .
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi
RUN yarn install --frozen-lockfile
STOPSIGNAL SIGINT
CMD ["poetry", "run", "web"]