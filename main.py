from fastapi import FastAPI

from routers import search, plan, course, health

app = FastAPI(title="Cambodia AI Server", version="1.4.0")

app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(plan.router, prefix="/plan", tags=["plan"])
app.include_router(course.router, prefix="/course", tags=["course"])
app.include_router(health.router, tags=["health"])