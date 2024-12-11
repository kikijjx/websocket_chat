
## Запуск

1. Установить виртуальное окружение:
```bash
python -m venv venv
```
2. Запустить окружение:
```bash
venv/scripts/activate
```
3. Установить зависимости:
```bash
pip install -r requirements.txt
```
4. Запустить Redis
```bash
docker-compose up --build
```
4. Отредактировать файл .env (пример в файле .env.example):
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
SERVER_HOST=0.0.0.0
SERVER_PORT=8888
```
5. Запустить приложение:
```bash
python main.py
```
6. Открыть сайт по указанному в .env адресе (адрес дублируется в терминале при запуске сервера)
