import logging
import os

from dotenv import load_dotenv
from github import Auth, GithubIntegration

from acedev.api.api import get_api
from acedev.service.agent.openai_agent import OpenAIAgent
from acedev.service.openai_service import OpenAIService

logging.basicConfig(level=logging.INFO)

load_dotenv()

auth = Auth.AppAuth(
    app_id=int(os.environ["GHE_APP_ID"]), private_key=os.environ["GHE_PRIVATE_KEY"]
)

ghe_client = GithubIntegration(
    base_url=f"https://{os.environ['GHE_HOSTNAME']}", auth=auth
)

openai_service = OpenAIService()
openai_agent = OpenAIAgent(model="gpt-4-turbo-preview", temperature=0.0, openai_service=openai_service)


"""
You should have access to the project now. Your task is to add an endpoint that returns the current timestamp.

Here's what I expect from you now: 
1. Check out the high-level overview of the project. 
2. Expand any function or class if needed. 
3. Give me a 4-5 bullet-point plan for implementation."""

main = get_api(ghe_client, openai_service, openai_agent)
