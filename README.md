# public.safe.system

Система анализа безопасности на основе компьютерного зрения (Python + OpenCV).

---

## Требования

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Mac / Windows / Linux)
- Git

---

## Быстрый старт

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/BekdauletBol/public.safe.system.VSCode.git
cd public.safe.system.VSCode
```

### 2. Убедитесь что Docker Desktop запущен

На Mac откройте приложение **Docker Desktop** и дождитесь статуса **"Engine running"** (зелёная иконка внизу).

### 3. Запустите проект

```bash
docker-compose up -d
```

Приложение будет доступно по адресу: **http://localhost:8000**

### 4. Остановить проект

```bash
docker-compose down
```

---

## Частые ошибки и решения

### ❌ `Cannot connect to the Docker daemon`

Docker Desktop не запущен. Откройте приложение Docker Desktop и подождите пока двигатель запустится.

### ❌ `The container name "/public-safe-app" is already in use`

Старый контейнер остался в системе. Удалите его:

```bash
docker rm -f public-safe-app
```

Затем снова запустите:

```bash
docker-compose up -d
```

### ❌ `no configuration file provided: not found`

Вы запускаете команду не из папки проекта. Перейдите в нужную папку:

```bash
cd ~/путь/к/public.safe.system.VSCode
docker-compose up -d
```

### ❌ `ImportError: libGL.so.1`

Эта ошибка была исправлена в текущем Dockerfile — добавлены библиотеки `libgl1` и `libglib2.0-0` в runtime-образ.

---

## Структура проекта

```
public.safe.system.VSCode/
├── analysis/               # Модули анализа
│   ├── system_health/
│   ├── analyze_phase1.py
│   ├── analyze_phase2.py
│   ├── analyze_phase4.py
│   ├── build_health_report.py
│   └── final_report.py
├── configs/                # Конфигурационные файлы
├── dashboard/              # Веб-интерфейс
│   └── index.html
├── data/                   # Данные (монтируется в контейнер)
├── edge/                   # Edge-компоненты
├── server/                 # Серверная часть
│   └── main.py
├── tools/                  # Утилиты
├── Dockerfile              # Сборка образа (multi-stage)
├── docker-compose.yml      # Запуск контейнера
└── requirements.txt        # Python-зависимости
```

---

## Разработка без Docker

```bash
python -m venv venv
source venv/bin/activate        
pip install -r requirements.txt
python server/main.py

ipconfig getifaddr en0

uvicorn server.main:app --host 0.0.0.0 --port 8000 --ssl-keyfile key.pem --ssl-certfile cert.pem
```

---

## Пересборка образа после изменений

```bash
docker-compose down
docker-compose up -d --build

```