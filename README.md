# Foodgram
### Описание
Социальная сеть с гастрономической тематикой. В ней пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Сервис «Список покупок» позволяет пользователям создавать список продуктов, которые нужно купить для приготовления выбранных блюд.
### Технологии
- Python 3.7
- Django 2.2.19
- React.js 17.0.1
- PostgreSQL 13.0
- Nginx 1.19.3
- Docker 20.10.12 (Docker Compose 2.6.1)
### Запуск проекта
- Склонировать репозиторий
(Все дальнейшие действия выполнять из папки /infra)
- Создать и заполнить .env файл по примеру:
```
SECRET_KEY=<КЛЮЧ>
DB_NAME=postgres
POSTGRES_USER=<ИМЯ ПОЛЬЗОВАТЕЛЯ>
POSTGRES_PASSWORD=<ПАРОЛЬ ПОЛЬЗОВАТЕЛЯ>
DB_HOST=db
DB_PORT=5432
```
- Запустить сборку контейнеров:
```
docker-compose up -d --build
```
- (Опционально) Образы берутся с DockerHub, при внесении изменений в проект необходимо пересобирать образы:
```
# docker-compose.yml

frontend:
    image: hoouinkema/foodgram-frontend:v1.01

backend:
    image: hoouinkema/foodgram-backend:v1.01
```
Заменить на:
```
# docker-compose.yml

frontend:
  build: ../frontend

backend:
  build: ../backend
```
- Перейти в контейнер с Django:
```
sudo docker-compose exec backend bash
```
- Выполнить миграции:
```
python manage.py migrate
```
- Собрать статику:
```
python manage.py collectstatic
```
- (Опционально) Создать суперпользователя:
```
python manage.py createsuperuser
```
- (Опционально) Заполнить БД ингредиентами:
(Для просмотра id запущенных контейнеров: ```docker ps```)
```
docker cp ../data/ingredients.json [ID КОНТЕЙНЕРА BACKEND]:app/
```
```
sudo docker-compose exec backend python manage.py loaddata ingredients.json
```
- (Опционально) Заполнить БД тэгами:
```
docker cp ../data/tags.json [ID КОНТЕЙНЕРА BACKEND]:app/
```
```
sudo docker-compose exec backend python manage.py loaddata tags.json
```
Проект доступен по адресу http://localhost/ (админ-зона http://localhost/admin/)
