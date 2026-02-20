"""解析本地 .agents/skills 目录，加载 Claude Agent Skills 格式的技能"""

from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass

import yaml

# 假设项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
SKILLS_DIR = PROJECT_ROOT / ".agents" / "skills"


@dataclass
class AgentSkill:
    """内部表示的 Skill 数据"""
    name: str
    description: str
    instructions: str
    trigger_keywords: list[str]
    folder_path: str


def load_all_skills() -> list[AgentSkill]:
    """扫描目录，解析所有 SKILL.md"""
    skills = []

    if not SKILLS_DIR.exists() or not SKILLS_DIR.is_dir():
        return skills

    # 遍历 .agents/skills 下的所有子文件夹
    for entry in os.scandir(SKILLS_DIR):
        if entry.is_dir():
            skill_md_path = Path(entry.path) / "SKILL.md"
            if skill_md_path.exists() and skill_md_path.is_file():
                try:
                    with open(skill_md_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    skill = _parse_skill_md(content, entry.path)
                    if skill:
                        skills.append(skill)
                except Exception as e:
                    print(f"Failed to load skill from {skill_md_path}: {e}")

    return skills


def _parse_skill_md(content: str, folder_path: str) -> AgentSkill | None:
    """粗略解析 Markdown 的 YAML Frontmatter 和正文指令"""
    if not content.startswith("---"):
        return None

    # 分割 yaml 块和正文
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None

    yaml_text = parts[1].strip()
    instructions = parts[2].strip()

    try:
        metadata = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return None

    if not metadata or not isinstance(metadata, dict):
        return None

    name = metadata.get("name")
    description = metadata.get("description")

    if not name or not description:
        return None

    # 默认触发词（如果 yaml 未提供，用名称回退）
    trigger_keywords = metadata.get("trigger_keywords", [name])

    return AgentSkill(
        name=name,
        description=description,
        instructions=instructions,
        trigger_keywords=trigger_keywords,
        folder_path=folder_path,
    )
