import logging
from typing import Sequence, Type, TypeVar

from pydantic import BaseModel

from factory.chat_model import ChatModelFactory, ChatModelFactoryOptions
from model.model import ChatMessage, ModelName, Role
from acedev.service.model import (
    Action,
    CreatePullRequestResponse,
    FileAction,
    PullRequest,
    UpdatePullRequestResponse, SymbolLookup, SymbolLookupPlan, File,
)
from acedev.service.project import Project
from acedev.service.prompts import (
    create_pull_request_prompt,
    update_pull_request_prompt, plan_symbol_lookup_prompt,
)
from service.llm import LLMService
from acedev.utils.prompts import get_format_instructions

logger = logging.getLogger(__name__)

T_BaseModel = TypeVar("T_BaseModel", bound=BaseModel)


class CodingService:
    def __init__(self, llm: LLMService, model_factory: ChatModelFactory):
        self.llm = llm
        self.model = model_factory.create_gpt4_turbo(
            ChatModelFactoryOptions.defaults(
                model_name=ModelName.GPT_4_TURBO,
                temperature=0.0,
                model_kwargs={"response_format": {"type": "json_object"}},
            )
        )

    def create_pull_request(self, task: str, project: Project) -> PullRequest:
        try:
            repo_map = project.print_repo_map()
            symbol_lookup_plan = self._plan_symbol_lookup(task, repo_map)
            # symbol_definitions = []
            # for lookup in symbol_lookup_plan.lookups:
            # symbol_definitions.append(
            #     project.print_symbol(symbol=lookup.symbol, path=lookup.path)
            # )

            relevant_project_files = []
            for lookup in symbol_lookup_plan.lookups:
                relevant_project_files.append(
                    project.get_file(lookup.path)
                )
            pull_request_plan = self._plan_pull_request(task, relevant_project_files)
            branch = project.checkout_new_branch(pull_request_plan.branch)
            self._apply_changes(
                project=project, actions=pull_request_plan.actions, branch=branch
            )

            return project.create_pull_request(
                title=pull_request_plan.title, body=pull_request_plan.body, branch=branch
            )
        except Exception as e:
            error_message = f"Failed to create pull request for {project}."
            logger.exception(error_message)
            raise CodingServiceException(error_message) from e

    def update_pull_request(
            self, pull_request_id: int, task: str, project: Project
    ) -> PullRequest:
        try:
            pull_request = project.get_pull_request(_id=pull_request_id)
            branch = pull_request.head_ref
            project_files = project.get_files(branch=branch)
            completion_result = self._get_llm_completion(
                _prompt=update_pull_request_prompt(
                    comment=task,
                    pull_request=pull_request,
                    project_files=project_files,
                    output_format_instruction=get_format_instructions(
                        UpdatePullRequestResponse
                    ),
                ),
                response_model=UpdatePullRequestResponse,
            )
            self._apply_changes(
                project=project, actions=completion_result.actions, branch=branch
            )
            return project.get_pull_request(_id=pull_request_id)
        except Exception as e:
            error_message = f"Failed to update pull request for {project}."
            logger.exception(error_message)
            raise CodingServiceException(error_message) from e

    @staticmethod
    def _apply_changes(
            project: Project, actions: Sequence[FileAction], branch: str
    ) -> None:
        for file_action in actions:
            if file_action.action == Action.CREATE:
                project.create_file(file_action.file, branch)
            elif file_action.action == Action.UPDATE:
                project.update_file(file_action.file, branch)
            elif file_action.action == Action.DELETE:
                project.delete_file(file_action.file, branch)

    def _plan_symbol_lookup(self, task: str, repo_map: str) -> SymbolLookupPlan:
        return self._get_llm_completion(
            _prompt=plan_symbol_lookup_prompt(
                task=task,
                project_outline=repo_map,
                output_format_instruction=get_format_instructions(
                    SymbolLookupPlan
                ),
            ),
            response_model=SymbolLookupPlan,
        )

    def _plan_pull_request(self, task: str, project_files: Sequence[File]) -> CreatePullRequestResponse:
        return self._get_llm_completion(
            _prompt=create_pull_request_prompt(
                task=task,
                project_files=project_files,
                output_format_instruction=get_format_instructions(
                    CreatePullRequestResponse
                ),
            ),
            response_model=CreatePullRequestResponse,
        )

    def _get_llm_completion(
            self, _prompt: str, response_model: Type[T_BaseModel]
    ) -> T_BaseModel:
        """Get a completion from LLM given a prompt. Convert the response to a Pydantic model."""

        logger.info(f"LLM prompt: {_prompt}")

        response = self.llm.chat(
            model=self.model,
            messages=[
                ChatMessage(
                    role=Role.SYSTEM,
                    content="You are a helpful assistant designed to output JSON.",
                ),
                ChatMessage(role=Role.HUMAN, content=_prompt),
            ],
        )

        logger.info(f"LLM response: {response.content}")

        return response_model.model_validate_json(response.content)


class CodingServiceException(Exception):
    def __init(self, message: str) -> None:
        super().__init__(message)
