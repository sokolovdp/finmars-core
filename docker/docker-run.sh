
# docker run --name finmars-redis -d redis:3.0
# docker run --name finmars-db -e POSTGRES_PASSWORD=finmars -d postgres:9.5

# docker run --rm=true -p 8000:8000 -i -t finmars:latest

docker run --link finmars-db:postgres --link finmars-redis:redis --rm=true -p 8080:8080 -i -t finmars:latest
