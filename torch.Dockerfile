FROM nvidia/cuda:11.6.1-runtime-ubuntu20.04
WORKDIR /code
ENV \
  DEBIAN_FRONTEND=noninteractive \
  PIP_DEFAULT_TIMEOUT=100 \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  # This disables the cache dir: https://github.com/pypa/pip/issues/5735
  PIP_NO_CACHE_DIR=off \
  POETRY_VIRTUALENVS_IN_PROJECT=true \
  PRE_COMMIT_HOME=.pre-commit-home \
  PYENV_ROOT=/root/.pyenv \
  PYTHONFAULTHANDLER=1 \
  PYTHONPATH=/code \
  PYTHONUNBUFFERED=1

COPY nodesource.gpg ./
RUN \
  echo 'deb [signed-by=/code/nodesource.gpg] https://deb.nodesource.com/node_16.x focal main' \
    >/etc/apt/sources.list.d/nodesource.list && \
  apt update && \
  apt install -y \
    build-essential \
    curl \
    git \
    libbz2-dev \
    libffi-dev \
    liblzma-dev \
    libncursesw5-dev \
    libreadline-dev \
    libsqlite3-dev \
    libssl-dev \
    libxml2-dev \
    libxmlsec1-dev \
    llvm \
    make \
    nodejs \
    tk-dev \
    wget \
    xz-utils \
    zlib1g-dev && \
  rm -rf /var/lib/apt/lists/* && \
  git config --global --add safe.directory /code

WORKDIR /root
RUN git clone --depth=1 https://github.com/pyenv/pyenv.git .pyenv
ENV PATH="${PYENV_ROOT}/shims:${PYENV_ROOT}/bin:${PATH}"
RUN pyenv install 3.10.4 && pyenv global 3.10.4
WORKDIR /code

COPY poetry-requirements.txt poetry.lock pyproject.toml ./
RUN \
  pip install -r poetry-requirements.txt && \
  poetry install --no-interaction --no-ansi --extras torch && \
  rm -rf /root/.cache/pypoetry

ENV VIRTUAL_ENV=/code/.venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

RUN python -c "import nltk; nltk.download('punkt')"

COPY ui/package*.json ui/
RUN npm --prefix ui ci

COPY . .

CMD ["npm", "--prefix", "ui", "run", "dev"]
