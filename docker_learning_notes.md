# Docker - Learning Notes & Resources

ok so Docker... first thing to get is WHY it matters. basically: same app, diff laptop/server → no "it works on my machine". containers isolate everything. 
very similar idea to a lightweight VM, but faster bc they share the host kernel.

---

## random notes
- install it from https://docs.docker.com/get-docker/
- run `docker run hello-world` to see if it works. if not, restart the daemon (happens a lot on mac lol)
- containers vs images → image = recipe, container = cake 🍰
- try `docker ps -a` often, helps keep track of what’s running / stopped
- remember to `docker system prune` sometimes or disk fills up

## building stuff
the Dockerfile syntax is super simple but tricky at first.
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
```
→ that’s enough to run a Flask app. but if you rebuild a lot, move the COPY after installing deps to use caching.

### things to google
- “docker layer caching explained”  
- “docker context size too big”  
- “.dockerignore examples”  

also good to know: alpine images are super small, but sometimes they miss libraries (esp for numpy / pandas).

---

## docker compose
honestly, Compose is underrated. it makes local dev so much easier.  
`docker-compose up` and boom, multi-container app.

```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8080:80"
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: example
```
that + a `.env` file and you’re golden.

---

## useful links
- https://www.youtube.com/watch?v=pTFZFxd4hOI (Nana’s video – gold)
- Bret Fisher’s “Docker Mastery” course (Udemy)
- https://labs.play-with-docker.com/ → no setup needed
- https://github.com/wagoodman/dive → see image layers
- https://github.com/aquasecurity/trivy → security scans

## debugging notes
- use `docker logs` a lot.  
- also `docker exec -it <container> bash` is your best friend.  
- if networking fails, check `docker network ls` and inspect the bridge.

---

random thought: once you get comfy, try deploying a container to Cloud Run or Fargate. it’s wild how easy it is.

also check: multi-stage builds. they make images like 10x smaller.  
and remember — docker in docker is a rabbit hole 🕳️🐇 (don’t unless you really need to).

end of notes for now 🐋
