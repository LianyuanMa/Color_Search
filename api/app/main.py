from fastapi import FastAPI
from Routers import user,server
#uvicorn main:app --reload

app = FastAPI()
app.include_router(user.router)
app.include_router(server.router)

@app.get("/healthcheck")
def healthcheck():
    return {"status": "healthy"}
