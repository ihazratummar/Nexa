import os
from pathlib import Path
from typing import Optional, List

import math
import yaml
from loguru import logger
from pydantic import BaseModel, Field


# ─── Data Models ──────────────────────────────────────────────────────


class CommandArgs(BaseModel):
    """Represents a single argument for a command"""
    name: str
    type: str = "string"
    description: Optional[str] = None
    required: bool = False
    example: Optional[str] = None

class CommandInfo(BaseModel):
    """Represents a command info"""
    name: str
    description: Optional[str] = None
    usage: Optional[str] = None
    args: Optional[List[CommandArgs]] = None
    output: Optional[str] = None
    permissions: Optional[str] = None
    notes: Optional[str] = None

class CommandCategory(BaseModel):
    """Represents a command category"""
    name: str
    id: str
    description: Optional[str] = None
    emoji: Optional[str] = None
    commands: List[CommandInfo] = Field(default_factory=list)

class HelpData(BaseModel):
    """Root model for the entire commands.yaml structure"""
    categories: List[CommandCategory] = Field(default_factory=list)

# ─── Loader ───────────────────────────────────────────────────────────

COMMANDS_PER_PAGE = 10

_help_data: Optional[HelpData] = None

BASE_DIR = Path(__file__).resolve().parents[3]  # adjust depending on depth

def load_help_data(path: str = "commands.yaml") -> HelpData:
    """
    Load and parse commands.yaml into validated pydantic models
    Caches the result so the file is only read once
    """
    global _help_data

    if _help_data is not None:
        return _help_data

    abs_path = BASE_DIR / path

    if not os.path.exists(abs_path):
        logger.warning(f"commands.yaml not found {abs_path}, using empty file help data.")
        _help_data = HelpData()
        return _help_data

    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

            _help_data = HelpData(**raw)
            logger.info(
                f"Loaded help data :{len(_help_data.categories)} categories, "
                f"{sum(len(c.commands) for c in _help_data.categories)} commands"
            )
    except Exception as e:
        logger.error(f"Failed to load help data {e}")
        _help_data = HelpData()

    return _help_data


def reload_help_data(path: str = "commands.yaml") -> HelpData:
    """Force re-load the commands.yaml (useful when editing in runtime)"""
    global _help_data
    _help_data = None
    return load_help_data(path)

# ─── Accessors ────────────────────────────────────────────────────────

def get_all_categories() -> List[CommandCategory]:
    """return all commands categories"""
    return load_help_data().categories

def get_category(category_id: str) -> Optional[CommandCategory]:
    """Get a single category by its id"""
    for category in load_help_data().categories:
        if category.id == category_id:
            return category
    return None

def get_commands_for_category(category_id: str) -> List[CommandInfo]:
    """Return all commands belongs to a category"""
    category = get_category(category_id)
    return category.commands if category else []


def get_commands_page(category_id: str, page: int = 1) -> tuple[List[CommandInfo], int]:
    """
    Return a page of commands (Up to COMMANDS_PER_PAGE) and the total page count.

    Args:
        category_id (str): The category id
        page (int, optional): The page to return. Defaults to 1.

    Returns:
        (commands_on_page, total_pages)
    """

    all_commands = get_commands_for_category(category_id=category_id)
    total_pages = max(1, math.ceil(len(all_commands)/ COMMANDS_PER_PAGE))
    page = max(1, min(page, total_pages))

    start = (page - 1) * COMMANDS_PER_PAGE
    end = start + COMMANDS_PER_PAGE

    return all_commands[start:end], total_pages


def get_command(command_name: str) -> Optional[CommandInfo]:
    """
    Find a command by its name (e.g. '/sticky add') across all categories.
    Case-insensitive match
    """

    target = command_name.strip().lower()
    for category in load_help_data().categories:
        for cmd in category.commands:
            if cmd.name.strip().lower() == target:
                return cmd
    return None

def get_category_for_command(command_name: str) -> Optional[CommandCategory]:
    """Find which category a command belongs to"""
    target = command_name.strip().lower()
    for category in load_help_data().categories:
        for cmd in category.commands:
            if cmd.name.strip().lower() == target:
                return category
    return None
