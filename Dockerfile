FROM fedora:31

WORKDIR /notebooks

RUN dnf update -y \
    && dnf install which procps-ng nmap-ncat python3 python3-pip -y

RUN if [ ! -e /usr/bin/pip ]; then ln -s /usr/bin/pip3.7 /usr/bin/pip ; fi \
    && if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3.7 /usr/bin/python; fi \
    && pip install --upgrade pip && pip --no-cache-dir install poetry

COPY pyproject.toml poetry.lock README.md ./
RUN poetry config virtualenvs.create false
RUN poetry install -n

RUN dnf clean all \
    && rm -rf /var/cache/dnf

RUN mkdir /.local \
    && chmod -R 777 /notebooks \
    && chmod -R 777 /.local

USER root
