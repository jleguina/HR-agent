from __future__ import annotations

import logging

from langchain.agents.agent import AgentOutputParser
from langchain.output_parsers.json import parse_json_markdown
from langchain.schema import AgentAction, AgentFinish, OutputParserException

from app.agent.tools import RespondTool

logger = logging.getLogger(__name__)


class CustomJSONOutputParser(AgentOutputParser):
    def parse(self, text: str) -> AgentAction | AgentFinish:
        try:
            response = parse_json_markdown(text)
            if isinstance(response, list):
                # gpt turbo frequently ignores the directive to emit a single action
                logger.warning("Got multiple tool responses: %s", response)
                response = response[0]

            if response["tool"] == RespondTool().name:  # type: ignore
                return AgentFinish({"output": response["tool_input"]}, text)
            else:
                return AgentAction(
                    response["tool"], response.get("tool_input", {}), text
                )
        except Exception as e:
            raise OutputParserException(f"Could not parse LLM output: {text}") from e

    @property
    def _type(self) -> str:
        return "json-agent"
