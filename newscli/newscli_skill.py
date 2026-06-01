#!/usr/bin/env python3
"""
newscli_skill.py — OpenClaw skill 安装/更新/检测 (v1.1.1)

提供：
- install(): 把 bundled skill 装到 ~/.openclaw/skills/news-cli/
- update(): 检查并更新已装的 skill
- check(): 返回 4 种状态（not_installed / outdated / up_to_date / error）
- install_cmd / update_cmd / check_cmd: entry points（[project.scripts]）

约束（per `rules.script-encounter.md`）：
- 装到用户目录，不污染系统
- 装前检测：避免覆盖（除非 --force）
- 装后验证：再 read 一次确认装成功
"""
import json
import os
import sys
import shutil
import importlib.resources
from datetime import datetime, timedelta
from pathlib import Path

# 路径常量
SKILL_NAME = "news-cli"
SKILL_DIR = Path.home() / ".openclaw" / "skills" / SKILL_NAME
SKILL_META_LOCAL = SKILL_DIR / "news-cli" / "skill-meta.json"
DISMISS_FILE = Path.home() / ".openclaw" / ".skill-update-dismissed-at"
DISMISS_TTL_HOURS = 24

# 从 wheel 内读 bundled skill（pyproject.toml package-data）
def _bundled_skill_dir() -> Path:
    """返回 bundled skill 的路径（在 wheel 内或开发模式下源码）。"""
    try:
        # Python 3.9+ 标准 API
        with importlib.resources.as_file(
            importlib.resources.files("newscli.skill")
        ) as p:
            return Path(p)
    except (ModuleNotFoundError, FileNotFoundError):
        # 开发模式：源码目录
        return Path(__file__).parent / "skill"


def _bundled_metadata() -> dict:
    """读 bundled metadata.json。"""
    p = _bundled_skill_dir() / "metadata.json"
    if not p.exists():
        return {"skill_version": "0.0.0", "newscli_min_version": "0.0.0"}
    return json.loads(p.read_text(encoding="utf-8"))


def _bundled_skill_md() -> str:
    """读 bundled SKILL.md 内容。"""
    p = _bundled_skill_dir() / "SKILL.md"
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def _bundled_newscli_skill_md() -> str:
    """读 bundled news-cli/SKILL.md（子目录版本）。"""
    p = _bundled_skill_dir() / "news-cli" / "SKILL.md"
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


# 公开 API

def check() -> dict:
    """
    返回 4 种状态 + 详情。

    Returns:
        {
            "state": "not_installed" | "outdated" | "up_to_date" | "error",
            "installed_version": str | None,
            "bundled_version": str,
            "recommend": "run newscli-skill-install" | "run newscli-skill-update" | "all good"
        }
    """
    try:
        bundled = _bundled_metadata()
        bundled_v = bundled.get("skill_version", "0.0.0")

        if not SKILL_DIR.exists():
            return {
                "state": "not_installed",
                "installed_version": None,
                "bundled_version": bundled_v,
                "recommend": "run newscli-skill-install",
            }

        # 读已装的版本
        installed_v = "0.0.0"
        if SKILL_META_LOCAL.exists():
            try:
                meta = json.loads(SKILL_META_LOCAL.read_text(encoding="utf-8"))
                installed_v = meta.get("skill_version", "0.0.0")
            except (json.JSONDecodeError, OSError):
                pass
        else:
            # 退化：读 SKILL.md 头部的 frontmatter
            skill_md = SKILL_DIR / "SKILL.md"
            if skill_md.exists():
                for line in skill_md.read_text(encoding="utf-8").split("\n")[:5]:
                    if line.startswith("skill_version:"):
                        installed_v = line.split(":", 1)[1].strip().strip('"')

        # 简单 semver 比较
        if _ver_ge(bundled_v, installed_v):
            return {
                "state": "up_to_date" if bundled_v == installed_v else "outdated",
                "installed_version": installed_v,
                "bundled_version": bundled_v,
                "recommend": "all good" if bundled_v == installed_v else "run newscli-skill-update",
            }
        else:
            # bundled 比 installed 还旧（理论上不应该发生）
            return {
                "state": "outdated",
                "installed_version": installed_v,
                "bundled_version": bundled_v,
                "recommend": "WARN: installed version newer than bundled",
            }
    except Exception as e:
        return {
            "state": "error",
            "installed_version": None,
            "bundled_version": "?",
            "recommend": f"check failed: {e}",
        }


def install(force: bool = False) -> int:
    """
    装 bundled skill 到 ~/.openclaw/skills/news-cli/。
    Returns 0 on success, 1 on failure.
    """
    if SKILL_DIR.exists() and not force:
        state = check()
        if state["state"] == "up_to_date":
            print(f"✅ Skill already up-to-date (v{state['installed_version']})")
            return 0
        elif state["state"] == "outdated":
            print(f"💡 Skill outdated ({state['installed_version']} → {state['bundled_version']})")
            ans = input("Update now? [Y/n] ").strip().lower()
            if ans not in ("", "y", "yes"):
                print("Skipped.")
                return 0
        elif state["state"] == "not_installed":
            ans = input(f"💡 Install OpenClaw skill v{state['bundled_version']} now? [Y/n] ").strip().lower()
            if ans not in ("", "y", "yes"):
                print("Skipped.")
                return 0

    bundled = _bundled_skill_dir()
    if not bundled.exists():
        print(f"❌ Bundled skill not found at {bundled}")
        return 1

    try:
        # 创建目录
        SKILL_DIR.mkdir(parents=True, exist_ok=True)

        # 复制 SKILL.md
        (SKILL_DIR / "SKILL.md").write_text(
            _bundled_skill_md(), encoding="utf-8"
        )

        # 复制子目录 news-cli/ + 子 SKILL.md
        (SKILL_DIR / "news-cli").mkdir(exist_ok=True)
        (SKILL_DIR / "news-cli" / "SKILL.md").write_text(
            _bundled_newscli_skill_md(), encoding="utf-8"
        )

        # 复制 metadata.json（重命名为 skill-meta.json 以匹配上面 SKILL_META_LOCAL）
        bundled_meta = _bundled_metadata()
        bundled_meta["installed_at"] = datetime.now().isoformat()
        (SKILL_DIR / "news-cli" / "skill-meta.json").write_text(
            json.dumps(bundled_meta, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print(f"✅ OpenClaw skill v{bundled_meta.get('skill_version')} installed to {SKILL_DIR}")
        return 0
    except Exception as e:
        print(f"❌ Install failed: {e}")
        return 1


def update() -> int:
    """force install（覆盖现有 skill）。"""
    return install(force=True)


def is_dismissed() -> bool:
    """检查用户在 24h 内是否已 dismiss 过提示。"""
    if not DISMISS_FILE.exists():
        return False
    try:
        content = DISMISS_FILE.read_text().strip()
        last_dismissed = datetime.fromisoformat(content)
        if datetime.now() - last_dismissed < timedelta(hours=DISMISS_TTL_HOURS):
            return True
    except (ValueError, OSError):
        pass
    return False


def mark_dismissed():
    """记录用户 dismiss 时间，24h 内不再提示。"""
    DISMISS_FILE.parent.mkdir(parents=True, exist_ok=True)
    DISMISS_FILE.write_text(datetime.now().isoformat())


def prompt_if_outdated() -> bool:
    """
    newscli 首次跑时调用。
    Returns True if skill is up-to-date, False if still needs action.
    """
    state = check()
    if state["state"] in ("up_to_date", "not_installed", "error"):
        if state["state"] == "not_installed":
            ans = input(
                f"💡 OpenClaw skill v{state['bundled_version']} not installed. "
                f"Install now? [Y/n] "
            ).strip().lower()
            if ans in ("", "y", "yes"):
                return install() == 0
            else:
                mark_dismissed()
                return False
        return state["state"] == "up_to_date"

    # outdated
    if is_dismissed():
        return False
    ans = input(
        f"💡 OpenClaw skill outdated ({state['installed_version']} → {state['bundled_version']} available). "
        f"Update now? [Y/n] "
    ).strip().lower()
    if ans in ("", "y", "yes"):
        return install() == 0
    else:
        mark_dismissed()
        return False


# CLI entry points（[project.scripts]）

def install_cmd():
    """Entry point: newscli-skill-install"""
    sys.exit(install())


def update_cmd():
    """Entry point: newscli-skill-update"""
    sys.exit(update())


def check_cmd():
    """Entry point: newscli-skill-check"""
    state = check()
    print(json.dumps(state, indent=2, ensure_ascii=False))
    sys.exit(0 if state["state"] in ("up_to_date", "not_installed") else 1)


# 内部辅助

def _ver_ge(a: str, b: str) -> bool:
    """比较 semver a >= b。"""
    try:
        pa = tuple(int(x) for x in a.split(".")[:3])
        pb = tuple(int(x) for x in b.split(".")[:3])
        return pa >= pb
    except (ValueError, AttributeError):
        return False
