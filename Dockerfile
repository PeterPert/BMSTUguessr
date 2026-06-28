# ============================================================
#  BMSTUguessr — Dockerized Desktop Application
# ============================================================
#  Этот образ запускает GUI-приложение на PySide6 (Qt6)
#  внутри контейнера, пробрасывая дисплей через X11.
#
#  Сборка:   docker build -t bmstuguessr .
#  Запуск:   см. docker-compose.yml или README
# ============================================================

# --------------- Stage 1: dependencies ---------------
FROM python:3.12-slim AS deps

WORKDIR /app

# Системные библиотеки, необходимые для Qt6 / PySide6
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1-mesa-glx \
        libegl1 \
        libglib2.0-0 \
        libfontconfig1 \
        libxkbcommon0 \
        libdbus-1-3 \
        libxcb-xinerama0 \
        libxcb-cursor0 \
        libxcb-icccm4 \
        libxcb-image0 \
        libxcb-keysyms1 \
        libxcb-randr0 \
        libxcb-render-util0 \
        libxcb-shape0 \
        x11-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --------------- Stage 2: application ---------------
FROM deps AS app

WORKDIR /app

# Копируем исходный код
COPY app/ app/
COPY main.py .

# Копируем данные (карты, фото, иконки, БД)
COPY data/ data/

# Метаданные образа
LABEL maintainer="BMSTUguessr Developer"
LABEL description="Baumanka GeoGuessr — desktop game in Docker"
LABEL version="1.0.0"

# Переменные среды для Qt
ENV QT_QPA_PLATFORM=xcb
ENV DISPLAY=:0

# Том для сохранения данных между запусками (БД, фото, темы)
VOLUME ["/app/data"]

# Точка входа
CMD ["python", "main.py"]
