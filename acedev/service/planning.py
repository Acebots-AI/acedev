import logging
from enum import Enum
from typing import Sequence, TypeVar

from langchain.agents import AgentExecutor
from pydantic import BaseModel

from acedev.service.model import SymbolLookupPlan
from acedev.service.project import Project
from acedev.service.prompts import plan_symbol_lookup_prompt, create_plan

logger = logging.getLogger(__name__)

T_BaseModel = TypeVar("T_BaseModel", bound=BaseModel)

DEFAULT_SYSTEM_PROMPT = """\
You are a software engineer who writes high-quality code. You are efficient and concise. You do what you're told.
"""


class ChangeType(str, Enum):
    CREATE = "create"
    DELETE = "delete"
    UPDATE = "update"


class Change(BaseModel):
    type: ChangeType
    file_path: str
    description: str


class Plan(BaseModel):
    description: str
    changes: Sequence[Change]


class Planner:
    def __init__(self, agent_executor: AgentExecutor, system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> None:
        # self.model = model
        self.agent_executor = agent_executor
        self.system_prompt = system_prompt


    def plan_with_react(self, task):
        return self.agent_executor.stream({"input": task})

    # def plan(self, task: str, project: Project) -> Plan:
    #     repo_map = project.print_repo_map()
    #
    #     symbol_lookup_prompt = plan_symbol_lookup_prompt(
    #         task=task,
    #         project_outline=repo_map,
    #         output_format_instruction=get_format_instructions(
    #             SymbolLookupPlan
    #         ),
    #     )
    #
    #     messages = [ChatMessage(role=Role.SYSTEM, content=self.system_prompt),
    #                 ChatMessage(role=Role.HUMAN, content=symbol_lookup_prompt)]
    #
    #     symbol_lookup_completion = self._get_llm_completion(messages)
    #     symbol_lookup_plan = SymbolLookupPlan.model_validate_json(symbol_lookup_completion.content)
    #     relevant_project_symbols = set()
    #
    #     for lookup in symbol_lookup_plan.lookups:
    #         relevant_project_symbols.add(
    #             project.print_symbol(lookup.symbol, lookup.path)
    #         )
    #
    #     create_plan_prompt = create_plan(symbols=relevant_project_symbols,
    #                                      output_format_instruction=get_format_instructions(Plan))
    #
    #     messages.extend([symbol_lookup_completion, ChatMessage(role=Role.HUMAN, content=create_plan_prompt)])
    #
    #     plan_completion = self._get_llm_completion(messages)
    #     return Plan.model_validate_json(plan_completion.content)
    #
    # def _get_llm_completion(self, messages: Sequence[ChatMessage]) -> ChatMessage:
    #     """Get a chat completion from LLM."""
    #
    #     logger.info(f"\nChat completion input:\n{messages}")
    #     response = self.model.invoke(list(messages))
    #     logger.info(f"\nChat completion output:\n{response.content}")
    #     return response
