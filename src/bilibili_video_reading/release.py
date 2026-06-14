from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


SKILL_NAME = "bilibili-video-reading"
MARKER = ".bvr-skill-source"


@dataclass(frozen=True)
class UninstallAction:
    label: str
    path: Path
    action: str
    reason: str


def path_from_env(name: str) -> Path | None:
    value = os.environ.get(name)
    if not value:
        return None
    return Path(value).expanduser()


def source_root() -> Path:
    env_root = path_from_env("BVR_PROJECT_DIR")
    if env_root is not None:
        return env_root
    return Path(__file__).resolve().parents[2]


def cmd_update(args: argparse.Namespace) -> int:
    root = source_root()
    installer = root / "scripts" / "install_remote.sh"
    if not installer.exists():
        raise SystemExit(f"Native installer script missing: {installer}")

    command = [str(installer)]
    if args.version:
        command.extend(["--version", args.version])
    if args.release_base_url:
        command.extend(["--release-base-url", args.release_base_url])
    if args.install_root:
        command.extend(["--install-root", args.install_root])
    if args.bin_dir:
        command.extend(["--bin-dir", args.bin_dir])
    if args.sync_skill:
        command.append("--sync-skill")
    else:
        command.append("--no-sync-skill")

    env = os.environ.copy()
    env.setdefault("BVR_INSTALL_LOG_PREFIX", "[bvr update]")
    return subprocess.run(command, check=False, env=env).returncode


def cmd_sync_skill(args: argparse.Namespace) -> int:
    root = source_root()
    sync_script = root / "scripts" / "sync_skill.sh"
    if not sync_script.exists():
        raise SystemExit(f"Skill sync script missing: {sync_script}")

    command = [str(sync_script)]
    if args.targets:
        command.extend(["--targets", args.targets])
    if args.force:
        command.append("--force")
    if args.dry_run:
        command.append("--dry-run")

    return subprocess.run(command, check=False, env=os.environ.copy()).returncode


def resolve_install_root(raw: str | None = None) -> Path:
    if raw:
        return Path(raw).expanduser()
    env_root = path_from_env("BVR_INSTALL_ROOT")
    if env_root is not None:
        return env_root
    return Path.home() / ".local" / "share" / "bvr"


def resolve_bin_dir(raw: str | None = None) -> Path:
    if raw:
        return Path(raw).expanduser()
    env_dir = path_from_env("BVR_BIN_DIR")
    if env_dir is not None:
        return env_dir
    return Path.home() / ".local" / "bin"


def skill_target_path(target: str) -> Path:
    direct = path_from_env(f"BVR_{target.upper()}_SKILL_DIR")
    if direct is not None:
        return direct

    if target == "codex":
        home = path_from_env("BVR_CODEX_HOME") or path_from_env("CODEX_HOME") or Path.home() / ".codex"
        return home / "skills" / SKILL_NAME
    if target == "cursor":
        home = path_from_env("BVR_CURSOR_HOME") or Path.home() / ".cursor"
        return home / "skills" / SKILL_NAME
    if target == "agents":
        home = path_from_env("BVR_AGENTS_HOME") or Path.home() / ".agents"
        return home / "skills" / SKILL_NAME
    if target == "claude":
        home = path_from_env("BVR_CLAUDE_HOME") or Path.home() / ".claude"
        return home / "skills" / SKILL_NAME
    raise ValueError(f"Unknown target {target}")


def launcher_candidates(bin_dir: Path) -> list[Path]:
    return [bin_dir / "bvr", bin_dir / "bvr.ps1", bin_dir / "bvr.cmd"]


def dangerous_removal_path(path: Path) -> bool:
    resolved = path.expanduser().resolve(strict=False)
    home = Path.home().resolve(strict=False)
    return resolved in {
        Path("/"),
        home,
        home / ".local",
        home / ".local" / "share",
        home / ".local" / "bin",
        home / ".codex",
        home / ".cursor",
        home / ".agents",
        home / ".claude",
    }


def launcher_is_bvr_owned(path: Path) -> bool:
    if not path.exists() and not path.is_symlink():
        return False
    if path.is_symlink():
        return True
    if not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")[:4096]
    except OSError:
        return False
    return "bilibili_video_reading.cli" in text and ("BVR_PROJECT_DIR" in text or "PYTHONPATH" in text)


def plan_native_uninstall(
    install_root: Path,
    bin_dir: Path,
    keep_skills: bool,
    targets: tuple[str, ...] = ("codex", "cursor", "agents", "claude"),
) -> list[UninstallAction]:
    actions: list[UninstallAction] = []

    if install_root.exists() or install_root.is_symlink():
        if dangerous_removal_path(install_root):
            actions.append(UninstallAction("install root", install_root, "skip", "unsafe parent path"))
        else:
            actions.append(UninstallAction("install root", install_root, "remove", "native release install root"))
    else:
        actions.append(UninstallAction("install root", install_root, "skip", "missing"))

    for launcher in launcher_candidates(bin_dir):
        if not launcher.exists() and not launcher.is_symlink():
            actions.append(UninstallAction("launcher", launcher, "skip", "missing"))
        elif launcher_is_bvr_owned(launcher):
            actions.append(UninstallAction("launcher", launcher, "remove", "generated bvr launcher"))
        else:
            actions.append(UninstallAction("launcher", launcher, "skip", "not generated by bvr"))

    if keep_skills:
        actions.append(UninstallAction("skill targets", Path("(all)"), "skip", "--keep-skills"))
        return actions

    seen: set[Path] = set()
    for target in targets:
        path = skill_target_path(target)
        key = path.expanduser().absolute()
        if key in seen:
            continue
        seen.add(key)
        label = f"skill {target}"
        if path.is_symlink():
            actions.append(UninstallAction(label, path, "remove", "owned symlink target"))
        elif path.exists() and (path / MARKER).exists():
            actions.append(UninstallAction(label, path, "remove", "marked bvr skill target"))
        elif path.exists():
            actions.append(UninstallAction(label, path, "skip", "unmarked skill target"))
        else:
            actions.append(UninstallAction(label, path, "skip", "missing"))

    return actions


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def print_uninstall_plan(actions: list[UninstallAction]) -> None:
    print("bvr uninstall plan:")
    for item in actions:
        print(f"  {item.action}: {item.label}: {item.path} ({item.reason})")


def cmd_uninstall(args: argparse.Namespace) -> int:
    install_root = resolve_install_root(args.install_root)
    bin_dir = resolve_bin_dir(args.bin_dir)
    actions = plan_native_uninstall(install_root, bin_dir, keep_skills=args.keep_skills)
    print_uninstall_plan(actions)

    if args.dry_run:
        return 0
    if not args.yes:
        print("Refusing to uninstall without --yes. Use --dry-run to preview only.", file=sys.stderr)
        return 2

    for item in actions:
        if item.action == "remove":
            remove_path(item.path)
            print(f"removed: {item.path}")
        else:
            print(f"skipped: {item.path} ({item.reason})")
    return 0
