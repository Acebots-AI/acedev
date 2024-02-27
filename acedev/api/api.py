import fastapi
from github import GithubIntegration
from starlette.middleware.cors import CORSMiddleware

from acedev.api import webhook, root
from acedev.api.settings import ApiSettings
from acedev.agent.openai_agent import OpenAIAgent
from acedev.service.openai_service import OpenAIService


def get_api(
    ghe_client: GithubIntegration,
    openai_service: OpenAIService,
    openai_agent: OpenAIAgent,
) -> fastapi.FastAPI:
    """Create and set up the API.

    Register routers, middleware and similar to get a working API.
    """

    api_settings = ApiSettings()

    # Create the FastAPI class. All standard settings are configured in
    # setting.ApiSettings
    api = fastapi.FastAPI(
        title=api_settings.title,
        description=api_settings.description,
        version=api_settings.version,
        redoc_url=api_settings.redoc_url,
        openapi_url=api_settings.openapi_url,
        docs_url=api_settings.docs_url,
        servers=api_settings.servers,
    )

    # Save the settings in the API:s state so they can be retrieved when needed
    # by injecting a dependency on the utility function
    # spotify_fastapi_utils.get_api_settings in the path. See example in
    # routers/root.py
    api.state.api_settings = api_settings

    api.state.ghe_client = ghe_client
    api.state.openai_service = openai_service
    api.state.openai_agent = openai_agent

    # Add CORS middleware, almost required if the API is to be used from a
    # browser. The CORS origins are configured in the settings.
    # https://en.wikipedia.org/wiki/Cross-origin_resource_sharing
    api.add_middleware(
        CORSMiddleware,
        allow_origins=api_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register the paths in the root router on the API.
    api.include_router(root.router)
    api.include_router(webhook.router, prefix="/v1")

    # define_exception_handlers(api)

    return api
