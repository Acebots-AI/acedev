import logging
import os

from dotenv import load_dotenv
from github import Auth, GithubIntegration

from acedev.agent.github_agent_factory import GitHubAgentFactory
from acedev.api.api import get_api
from acedev.agent.openai_agent_runner import OpenAIAgentRunner
from acedev.service.openai_service import OpenAIService

logging.basicConfig(level=logging.INFO)

logging.getLogger("LiteLLM").setLevel(logging.WARNING)

load_dotenv()

auth = Auth.AppAuth(
    app_id=int(os.environ["GITHUB_APP_ID"]),
    private_key=os.environ["GITHUB_APP_PRIVATE_KEY"],
)

ghe_client = GithubIntegration(
    base_url=f"https://{os.environ['GITHUB_HOSTNAME']}", auth=auth
)

github_agent_factory = GitHubAgentFactory()
openai_service = OpenAIService()
openai_agent = OpenAIAgentRunner(
    model="gpt-4-turbo-preview", temperature=0.0, openai_service=openai_service
)

main = get_api(
    ghe_client=ghe_client,
    openai_service=openai_service,
    openai_agent=openai_agent,
    github_agent_factory=github_agent_factory,
)
