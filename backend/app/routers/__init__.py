"""Routers package"""
# backend/app/routers/__init__.py
from .diagnosis import router as diagnosis_router
from .adversarial import router as adversarial_router
from .trajectory import router as trajectory_router
from .community import router as community_router
from .vitals import router as vitals_router
from .risk import router as risk_router
from .outbreak import router as outbreak_router
