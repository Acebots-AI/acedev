import fastapi

from acedev.api.dependencies import get_api_settings
from acedev.api.settings import ApiSettings

router = fastapi.APIRouter()


@router.get("/", summary="Root endpoint, can be used to see if API is up")
def get_root(
    api_settings: ApiSettings = fastapi.Depends(get_api_settings),
) -> str:
    """Root endpoint.

    Example of simple endpoint that returns a string. This endpoint is used by
    the Kubernetes healthcheck and must be present. The returned content does
    not matter.
    """
    return f"{api_settings.title}, version {api_settings.version}"
