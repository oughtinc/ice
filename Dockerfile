# FROM python:3.10.4-slim as build
FROM nvidia/cuda:11.6.1-runtime-ubuntu20.04

ENV DEBIAN_FRONTEND=noninteractive

# Install python & dependencies
RUN apt update && apt install -y --no-install-recommends \
  python3 \
  python3-pip \
  git \
  curl \
  make \
  build-essential \
  libssl-dev \
  zlib1g-dev \
  libbz2-dev \
  libreadline-dev \
  libsqlite3-dev \
  llvm \
  libncurses5-dev \
  xz-utils \
  tk-dev \
  libxml2-dev \
  libxmlsec1-dev \
  libffi-dev \
  liblzma-dev \
  libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Install specific python version using pyenv
ENV HOME="/root"
WORKDIR ${HOME}
RUN git clone --depth=1 https://github.com/pyenv/pyenv.git .pyenv
ENV PYENV_ROOT="${HOME}/.pyenv"
ENV PATH="${PYENV_ROOT}/shims:${PYENV_ROOT}/bin:${PATH}"

ENV PYTHON_VERSION="3.10.4"
RUN pyenv install ${PYTHON_VERSION}
RUN pyenv global ${PYTHON_VERSION}

ENV \
  PIP_DEFAULT_TIMEOUT=100 \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_NO_CACHE_DIR=off \
  POETRY_VIRTUALENVS_IN_PROJECT=true \
  PYTHONFAULTHANDLER=1 \
  PYTHONHASHSEED=random \
  PYTHONUNBUFFERED=1 \
  PRE_COMMIT_HOME=.pre-commit-home

WORKDIR /code

RUN git config --global --add safe.directory /code

COPY poetry-requirements.txt poetry.lock pyproject.toml /code/
RUN pip install -r poetry-requirements.txt
RUN poetry install --no-interaction --no-ansi --no-cache \
  && rm -rf /root/.cache/pypoetry

ENV VIRTUAL_ENV=/code/.venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

RUN python -c "import nltk; nltk.download('punkt')"

COPY . /code

CMD "scripts/runs-in-container/start-backend.sh"
