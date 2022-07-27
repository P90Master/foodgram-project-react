# Foodgram
### Описание
Социальная сеть с гастрономической тематикой. В ней пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Сервис «Список покупок» позволяет пользователям создавать список продуктов, которые нужно купить для приготовления выбранных блюд.
### Технологии
- Python 3.7
- Django 2.2.19
- React.js 17.0.1
- Docker 20.10.12 (Docker Compose 2.6.1)
### Запуск проекта
- Склонировать репозиторий
- Создать и заполнить .env файл в foodgram-project-react/infra/ по примеру:
```
SECRET_KEY=<КЛЮЧ>
DB_NAME=postgres
POSTGRES_USER=<ИМЯ ПОЛЬЗОВАТЕЛЯ>
POSTGRES_PASSWORD=<ПАРОЛЬ ПОЛЬЗОВАТЕЛЯ>
DB_HOST=db
DB_PORT=5432
```
(Все дальнейшие действия выполнять из папки /infra)
- Запустить сборку контейнеров:
```
docker-compose up -d --build
```
- Перейти в контейнер с Django:
```
sudo docker exec -it backend bash
```
- Выполнить миграции:
```
python manage.py migrate
```
- Собрать статику:
```
python manage.py collectstatic
```
- (Опционально) создать суперпользователя:
```
python manage.py createsuperuser
```
### Авторы
Telegram: @social_creditor
