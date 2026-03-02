## Данный репозиторий представляет собой frontend + backend приложение

# чтобы его запустить нужно ввести комманды:
brew install docker
brew install docker-compose 
brew install --cask docker

открыть Docker.Desctop 

запустить команду docker compose up -d 

Команда docker compose down -v используется для отстановке всех контейнеров с их кэшем 
(удалятся контейнеры, тома, сети )

## Описание переменных окружения
POSTGRES_DB - название базы данных
POSTGRES_USER - логин для авторизации бд
POSTGRES_PASSWORD - пароль для авторизации бд

## Полезные команды отладки

# Логи конкретного сервиса
docker compose logs -f backend
# Войти внутрь контейнера
docker compose exec backend sh
docker compose exec postgres psql -U appuser -d taskdb
# Просмотреть сети
docker network ls
docker network inspect docker-lab_default
# Просмотреть тома
docker volume ls


## Полезные команды Docker 

docker build -t myapp . # собрать образ
docker run -d -p 8080:80 myapp # запустить контейнер
docker images # список образов
docker ps # запущенные контейнеры
docker logs <container> # логи
docker exec -it <container> sh # войти внутрь

## Полезные команды Git

git checkout -b <branch> git add . 
git commit -m "message" 
git push origin <branch> 
git checkout main 
git merge <branch> 
git tag v1.0.0 
git log --oneline --graph 

## Docker Compose

docker compose up -d --build 
docker compose down                     
docker compose down -v 
docker compose logs -f <svc> 
docker compose exec <svc> sh 
docker compose ps 
docker network ls docker volume ls 