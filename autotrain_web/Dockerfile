# Указываем базовый образ, который содержит Python и все необходимые зависимости
FROM python:3.9

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /autotrain_web

# Копируем файлы requirements.txt в рабочую директорию контейнера
COPY requirements.txt .

# Устанавливаем зависимости проекта
RUN pip install -r requirements.txt

# Копируем все остальные файлы проекта в рабочую директорию контейнера
COPY . .

RUN python manage.py makemigrations
RUN python manage.py migrate

# Запускаем команду для запуска Django сервера
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
