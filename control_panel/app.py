from __future__ import annotations

from fastapi import FastAPI

from control_panel.routes.dashboard import router as dashboard_router
from control_panel.routes.proposals import router as proposals_router
from control_panel.routes.validation import router as validation_router
from control_panel.routes.worker_generator import router as worker_generator_router
from control_panel.routes.workers import router as workers_router
from control_panel.routes.worker_specs import router as worker_specs_router

app = FastAPI(title="TaskDock Control Panel MVP")

app.include_router(dashboard_router)
app.include_router(validation_router)
app.include_router(proposals_router)
app.include_router(workers_router)
app.include_router(worker_specs_router)
app.include_router(worker_generator_router)
