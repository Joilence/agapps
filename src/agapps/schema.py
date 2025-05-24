from typing_extensions import Literal
from pydantic import BaseModel
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
from abc import ABC, abstractmethod


class MCP(BaseModel):
    name: str
    command: str
    envs: Dict[str, str] = {}

class MCPConfig(BaseModel):
    path: Path
    type: Literal["global", "workspace"]
    servers: List[MCP]

class Rule(BaseModel):
    pattern: Path

    @property
    def word_count(self) -> int:
        try:
            return len(self.pattern.read_text().split())
        except (IOError, IsADirectoryError, FileNotFoundError):
            return 0

    @property
    def line_count(self) -> int:
        try:
            return len(self.pattern.read_text().splitlines())
        except (IOError, IsADirectoryError, FileNotFoundError):
            return 0

class RuleConfig(BaseModel):
    path: Path
    type: Literal["global", "workspace"]
    rules: List[Rule]

class Prompt(BaseModel):
    pattern: Path

    @property
    def word_count(self) -> int:
        try:
            return len(self.pattern.read_text().split())
        except (IOError, IsADirectoryError, FileNotFoundError):
            return 0

    @property
    def line_count(self) -> int:
        try:
            return len(self.pattern.read_text().splitlines())
        except (IOError, IsADirectoryError, FileNotFoundError):
            return 0

class PromptConfig(BaseModel):
    path: Path
    type: Literal["global", "workspace"]
    prompts: List[Prompt]

class AgentApp(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def get_mcps(self, workspace: Union[Path, str, None] = None) -> Union[List[MCPConfig], None]:
        pass

    @abstractmethod
    def get_rules(self, workspace: Union[Path, str, None] = None) -> Union[List[RuleConfig], None]:
        pass

    @abstractmethod
    def get_prompts(self, workspace: Union[Path, str, None] = None) -> Union[List[PromptConfig], None]:
        pass
