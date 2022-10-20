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
  PYTHONPATH=/code \
  PYTHONUNBUFFERED=1 \
  # Suppress this warning:
  #   None of PyTorch, TensorFlow >= 2.0, or Flax have been found. Models won't be available
  #   and only tokenizers, configuration and file/data utilities can be used.
  # TODO: Suppress only this warning instead of all warnings.
  TRANSFORMERS_VERBOSITY=error

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
  git config --global --add safe.directory /code && \
  npm install -g concurrently

COPY poetry-requirements.txt poetry.lock pyproject.toml ./
ARG poetry_install_args=""
RUN \
  pip install -r poetry-requirements.txt && \
  poetry install --no-interaction --no-ansi $poetry_install_args && \
  rm -rf /root/.cache/pypoetry

ENV VIRTUAL_ENV=/code/.venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

RUN python -c "import nltk; nltk.download('punkt')"

COPY ui/package.json ui/package-lock.json ui/
COPY ui/patches/*.patch ui/patches/
COPY kelvin/package.json kelvin/package-lock.json kelvin/
COPY kelvin/patches/*.patch kelvin/patches/

RUN npm --prefix ui ci
RUN npm --prefix kelvin ci

COPY . .

CMD ["concurrently", "uvicorn ice.routes.app:app --host 0.0.0.0 --port 8935 --reload", "npm --prefix ui run dev", "npm --prefix kelvin run dev"]
