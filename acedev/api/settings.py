from typing import Optional


class ApiSettings:
    """Class storing the mandatory settings.

    This class stores the mandatory settings for the API. It can be extended
    with optional settings in the service.

    Pydantics BaseSetting class allows override of these settings using the
    corresponding environment variable, prefixed by the `env_prefix` configured
    for the class (`api_` in this case). Complex variables are loaded by JSON.

    As such, the CORS origins can be overridden for local development with:
    API_CORS_ORIGINS='["http://localhost:3000"]' uvicorn main:main

    Attributes:
        title: API title, exposed through OpenAPI spec.
        description: API description, exposed through OpenAPI spec.
        version: Semver version of the API, exposed through OpenAPI spec.

        redoc_url: Path to interactive Redoc pages. Disabled if omitted.
        openapi_url: Path to OpenAPI JSON spec. Disabled if omitted.
        docs_url: Path to interactive doc pages (OpenAPI/Swagger). Disabled if
            omitted.

        servers: Specify servers according to the OpenAPI specification.
            Additionally, this field can be used if there are both production
            and testing servers.
            Example:
            servers = [
              {"url": "https://dev.acebots.ai", "description": "Production"},
            ]

        cors_origins: List of CORS origins. Can be omitted if the API is not
            meant to be called from frontends. The attribute is used in api.py to
            register the middleware.

        Config:
            Class with additional settings for Pydantic.
            env_prefix sets a prefix for setting these settings through
            environment variables
    """

    title: str = "acedev"
    description: str = "AceDev"
    version: str = "1.0.0"
    redoc_url: Optional[str] = "/redoc"
    openapi_url: Optional[str] = "/openapi.json"
    docs_url: Optional[str] = "/docs"

    servers: Optional[list[dict[str, str]]] = [
        {"url": "http://localhost:8000", "description": "Local"},
    ]

    # CORS origins.
    cors_origins: list[str] = [
        "http://localhost:8000",
    ]

    class Config:
        env_prefix = "api_"
