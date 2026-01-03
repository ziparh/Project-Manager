FROM python:3.13.7-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt update && apt upgrade -y

COPY pyproject.toml uv.lock ./
RUN pip install --upgrade pip
RUN pip install "uv==0.9.5"
RUN uv pip install --system --no-cache --requirement pyproject.toml

COPY . .

ENV PYTHONPATH=/app/src

RUN chmod +x src/prestart.sh

ENTRYPOINT ["./src/prestart.sh"]
CMD ["uv", "run", "src/main.py"]