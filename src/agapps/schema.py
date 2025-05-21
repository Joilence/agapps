from pydantic import BaseModel
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
from abc import ABC, abstractmethod


class MCP(BaseModel):
    name: str
    command: str
    envs: Dict[str, str] = {}


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


class AgentApp(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def get_mcps(self) -> List[MCP]:
        pass

    @abstractmethod
    def get_mcp_config_paths(self) -> List[Path]:
        """Get the list of file paths from which MCP configurations are loaded."""
        pass

    @abstractmethod
    def get_global_rules(self) -> List[Rule]:
        pass

    @abstractmethod
    def get_workspace_rules(self, workspace: Union[Path, str]) -> List[Rule]:
        pass 