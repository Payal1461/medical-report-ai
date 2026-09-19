from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401
from app.api import auth_routes, report_routes, dashboard_routes, trend_routes

app = FastAPI(title="AI Medical Report Explainer & PHR")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(report_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(trend_routes.router)


@app.get("/")
def root():
    return {"status": "ok"}