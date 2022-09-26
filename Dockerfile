FROM python:3.10.4-slim
WORKDIR /code
ENV \
  DEBIAN_FRONTEND=noninteractive \
  PIP_DEFAULT_TIMEOUT=100 \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  # This disables the cache dir: https://github.com/pypa/pip/issues/5735
  PIP_NO_CACHE_DIR=off \
  POETRY_VIRTUALENVS_IN_PROJECT=true \
  PRE_COMMIT_HOME=.pre-commit-home \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1

COPY nodesource.gpg ./
RUN \
  echo 'deb [signed-by=/code/nodesource.gpg] https://deb.nodesource.com/node_16.x focal main' \
    >/etc/apt/sources.list.d/nodesource.list && \
  apt update && \
  apt install -y \
    build-essential \
    git \
    nodejs && \
  rm -rf /var/lib/apt/lists/* && \
  git config --global --add safe.directory /code

COPY poetry-requirements.txt poetry.lock pyproject.toml ./
ARG poetry_install_args=""
RUN \
  pip install -r poetry-requirements.txt && \
  poetry install --no-interaction --no-ansi $poetry_install_args && \
  rm -rf /root/.cache/pypoetry

ENV VIRTUAL_ENV=/code/.venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

RUN python -c "import nltk; nltk.download('punkt')"

COPY ui/package*.json ui/
RUN npm --prefix ui ci

COPY . .

CMD ["sleep", "infinity"]
