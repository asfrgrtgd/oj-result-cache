FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends clang libclang-dev llvm \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /app/requirements.txt
RUN uv pip install -r requirements.txt

COPY . /app

CMD ["python", "oj_hash.py"]
