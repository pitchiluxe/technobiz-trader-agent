"""API routes package."""

from api.routes.config  import router as config_router
from api.routes.risk    import router as risk_router
from api.routes.signals import router as signals_router
from api.routes.trades  import router as trades_router
from api.routes.trends  import router as trends_router

__all__ = ["trends_router", "signals_router", "trades_router", "config_router", "risk_router"]
