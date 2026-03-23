from fastapi import FastAPI
from routers import search, plan, course, health

app = FastAPI(title="Travel AI Server")

app.include_router(health.router)
app.include_router(search.router, prefix="/search")
app.include_router(plan.router, prefix="/plan")
app.include_router(course.router, prefix="/course")