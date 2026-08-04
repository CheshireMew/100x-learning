from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = SKILL_ROOT / "assets" / "private-library"
HOME_TEMPLATE = ASSET_ROOT / "Home.md"
WRITING_CONFIG_TEMPLATE = ASSET_ROOT / "writing-memory.json"
CONTENT_STRATEGY_TEMPLATE = ASSET_ROOT / "content-strategy.md"
TOPIC_PORTFOLIO_TEMPLATE = ASSET_ROOT / "topic-portfolio.md"
PUBLISHED_REVIEW_TEMPLATE = ASSET_ROOT / "published-content-review.md"

LIBRARY_SCHEMA = "100x-learning-private-library"
LIBRARY_VERSION = 2
MANIFEST_RELATIVE = Path(".100x-learning/library.json")
DEFAULT_CONFIG_RELATIVE = Path(".100x-learning/config.json")

REQUIRED_DIRECTORIES = (
    Path("00-Inbox"),
    Path("10-Knowledge"),
    Path("20-Sources"),
    Path("20-Sources/Articles"),
    Path("20-Sources/Content Cases"),
    Path("20-Sources/Social Posts/Content Cases/完整短内容"),
    Path("20-Sources/Hook Library"),
    Path("30-Projects"),
    Path("40-Outputs/Writing"),
    Path("50-Areas"),
    Path("60-Systems/Writing/style-guide"),
    Path("90-Archive"),
)


class LibraryError(ValueError):
    pass


@dataclass(frozen=True)
class LibraryLayout:
    root: Path

    @property
    def manifest(self) -> Path:
        return self.root / MANIFEST_RELATIVE

    @property
    def home(self) -> Path:
        return self.root / "Home.md"

    @property
    def knowledge(self) -> Path:
        return self.root / "10-Knowledge"

    @property
    def sources(self) -> Path:
        return self.root / "20-Sources"

    @property
    def article_sources(self) -> Path:
        return self.sources / "Articles"

    @property
    def social_cases(self) -> Path:
        return self.sources / "Social Posts" / "Content Cases"

    @property
    def case_index_root(self) -> Path:
        return self.sources / "Content Cases"

    @property
    def case_index(self) -> Path:
        return self.case_index_root / "内容案例索引.md"

    @property
    def hook_root(self) -> Path:
        return self.sources / "Hook Library"

    @property
    def hook_index(self) -> Path:
        return self.hook_root / "开头钩子索引.md"

    @property
    def writing_outputs(self) -> Path:
        return self.root / "40-Outputs" / "Writing"

    @property
    def writing_system(self) -> Path:
        return self.root / "60-Systems" / "Writing"

    @property
    def writing_config(self) -> Path:
        return self.writing_system / "writing-memory.json"

    @property
    def writing_index(self) -> Path:
        return self.writing_system / "published-content-index.jsonl"

    @property
    def content_strategy(self) -> Path:
        return self.writing_system / "content-strategy.md"

    @property
    def writing_templates(self) -> Path:
        return self.writing_system / "templates"

    @property
    def topic_portfolio_template(self) -> Path:
        return self.writing_templates / "topic-portfolio.md"

    @property
    def published_review_template(self) -> Path:
        return self.writing_templates / "published-content-review.md"

    @property
    def voice(self) -> Path:
        return self.writing_system / "style-guide" / "voice.md"


def default_config_path() -> Path:
    return Path.home() / DEFAULT_CONFIG_RELATIVE


def _absolute(path: Path) -> Path:
    return path.expanduser().resolve()


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LibraryError(f"文件不存在：{path}") from exc
    except json.JSONDecodeError as exc:
        raise LibraryError(f"{path} 不是有效 JSON：{exc}") from exc
    if not isinstance(value, dict):
        raise LibraryError(f"{path} 必须是 JSON 对象")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _manifest_value() -> dict[str, Any]:
    return {"schema": LIBRARY_SCHEMA, "version": LIBRARY_VERSION}


def _config_value(root: Path, marktree_cli: Path | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema": LIBRARY_SCHEMA,
        "version": LIBRARY_VERSION,
        "library_root": str(root),
    }
    if marktree_cli is not None:
        value["marktree_cli"] = str(marktree_cli)
    return value


def _check_manifest(path: Path) -> None:
    value = _json(path)
    if value.get("schema") != LIBRARY_SCHEMA:
        raise LibraryError(f"不是 100x-learning 私人知识库：{path}")
    if value.get("version") != LIBRARY_VERSION:
        raise LibraryError(
            f"私人知识库版本不受支持：{value.get('version')}，"
            f"当前需要 {LIBRARY_VERSION}"
        )


def _write_config(root: Path, config_path: Path | None) -> Path:
    target = _absolute(config_path or default_config_path())
    marktree_cli = None
    if target.is_file():
        current = _json(target)
        raw_cli = current.get("marktree_cli")
        if isinstance(raw_cli, str) and raw_cli.strip():
            marktree_cli = _absolute(Path(raw_cli))
    _write_json(target, _config_value(root, marktree_cli))
    return target


def configure_marktree_cli(
    cli_path: Path,
    config_path: Path | None = None,
) -> tuple[Path, Path]:
    config = _absolute(config_path or default_config_path())
    value = _json(config)
    root = resolve_library_root(config_path=config)
    executable = _absolute(cli_path)
    if not executable.is_file():
        raise LibraryError(f"marktree-cli 不存在：{executable}")
    probe = subprocess.run(
        [str(executable), "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if probe.returncode != 0 or "marktree-cli" not in probe.stdout:
        raise LibraryError(f"不是可用的 marktree-cli：{executable}")
    value.update(_config_value(root, executable))
    _write_json(config, value)
    return executable, config


def resolve_library_root(
    library_root: Path | None = None,
    config_path: Path | None = None,
    *,
    require_initialized: bool = True,
) -> Path:
    if library_root is not None:
        root = _absolute(library_root)
    else:
        config = _absolute(config_path or default_config_path())
        value = _json(config)
        if value.get("schema") != LIBRARY_SCHEMA:
            raise LibraryError(f"不是 100x-learning 私人库配置：{config}")
        raw_root = value.get("library_root")
        if not isinstance(raw_root, str) or not raw_root.strip():
            raise LibraryError(f"私人库配置缺少 library_root：{config}")
        root = _absolute(Path(raw_root))
    if not root.exists() or not root.is_dir():
        raise LibraryError(f"私人知识库目录不存在：{root}")
    if require_initialized:
        _check_manifest(root / MANIFEST_RELATIVE)
    return root


def _validate_structure(
    layout: LibraryLayout,
    *,
    require_manifest: bool,
) -> None:
    if not layout.root.exists() or not layout.root.is_dir():
        raise LibraryError(f"私人知识库目录不存在：{layout.root}")
    if require_manifest:
        _check_manifest(layout.manifest)
    if not layout.home.is_file():
        raise LibraryError(f"私人知识库缺少 Home.md：{layout.home}")
    missing = [
        str(relative)
        for relative in REQUIRED_DIRECTORIES
        if not (layout.root / relative).is_dir()
    ]
    if missing:
        raise LibraryError("私人知识库缺少目录：" + "、".join(missing))
    if not layout.writing_config.is_file():
        raise LibraryError(f"私人知识库缺少写作配置：{layout.writing_config}")
    writing = _json(layout.writing_config)
    for key in ("verified_first_party_url_prefixes", "published_article_roots"):
        value = writing.get(key)
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            raise LibraryError(f"{layout.writing_config}: {key} 必须是字符串数组")


def validate_library(root: Path) -> LibraryLayout:
    layout = LibraryLayout(_absolute(root))
    _validate_structure(layout, require_manifest=True)
    return layout


def _inside_skill(root: Path) -> bool:
    try:
        root.relative_to(SKILL_ROOT.resolve())
    except ValueError:
        return False
    return True


def _copy_template_if_missing(template: Path, target: Path) -> None:
    if target.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")


def initialize_library(
    root: Path,
    config_path: Path | None = None,
) -> tuple[LibraryLayout, Path, bool]:
    root = _absolute(root)
    if _inside_skill(root):
        raise LibraryError(
            "新私人知识库必须位于 100x-learning Skill 目录之外；"
            "已有的仓库内知识库请使用 adopt 接入"
        )
    manifest = root / MANIFEST_RELATIVE
    if root.exists() and any(root.iterdir()) and not manifest.exists():
        raise LibraryError(
            f"目标目录已有内容但尚未初始化：{root}；"
            "确认它是现有私人知识库时使用 adopt"
        )

    created = not manifest.exists()
    root.mkdir(parents=True, exist_ok=True)
    if manifest.exists():
        _check_manifest(manifest)
    else:
        _write_json(manifest, _manifest_value())
    for relative in REQUIRED_DIRECTORIES:
        (root / relative).mkdir(parents=True, exist_ok=True)

    layout = LibraryLayout(root)
    if not layout.home.exists():
        template = HOME_TEMPLATE.read_text(encoding="utf-8")
        layout.home.write_text(
            template.replace("{{DATE}}", date.today().isoformat()),
            encoding="utf-8",
        )
    _copy_template_if_missing(WRITING_CONFIG_TEMPLATE, layout.writing_config)
    _copy_template_if_missing(CONTENT_STRATEGY_TEMPLATE, layout.content_strategy)
    _copy_template_if_missing(
        TOPIC_PORTFOLIO_TEMPLATE,
        layout.topic_portfolio_template,
    )
    _copy_template_if_missing(
        PUBLISHED_REVIEW_TEMPLATE,
        layout.published_review_template,
    )

    layout = validate_library(root)
    config = _write_config(root, config_path)
    return layout, config, created


def adopt_library(
    root: Path,
    config_path: Path | None = None,
) -> tuple[LibraryLayout, Path]:
    root = _absolute(root)
    if not root.exists() or not root.is_dir():
        raise LibraryError(f"现有私人知识库目录不存在：{root}")
    layout = LibraryLayout(root)
    manifest = root / MANIFEST_RELATIVE
    if manifest.exists():
        _check_manifest(manifest)
    else:
        _validate_structure(layout, require_manifest=False)
        _write_json(manifest, _manifest_value())
    _validate_structure(layout, require_manifest=True)
    config = _write_config(root, config_path)
    return layout, config


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="初始化、接入、定位和验证 100x-learning 私人知识库"
    )
    parser.add_argument("--config", type=Path, help="本机私人库指针配置")
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="在 Skill 外部初始化新的私人知识库")
    init.add_argument("--root", type=Path, required=True)

    adopt = commands.add_parser("adopt", help="接入已有私人知识库")
    adopt.add_argument("--root", type=Path, required=True)

    show = commands.add_parser("show", help="显示当前私人知识库")
    show.add_argument("--root", type=Path)

    validate = commands.add_parser("validate", help="验证当前私人知识库")
    validate.add_argument("--root", type=Path)
    configure_marktree = commands.add_parser(
        "configure-marktree",
        help="配置由 Marktree 管理私人知识库写入和可选 Git",
    )
    configure_marktree.add_argument("--cli", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "init":
            layout, config, created = initialize_library(args.root, args.config)
            print(
                json.dumps(
                    {
                        "ok": True,
                        "action": "initialized" if created else "already-initialized",
                        "library_root": str(layout.root),
                        "config": str(config),
                        "version": LIBRARY_VERSION,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        if args.command == "adopt":
            layout, config = adopt_library(args.root, args.config)
            print(
                json.dumps(
                    {
                        "ok": True,
                        "action": "adopted",
                        "library_root": str(layout.root),
                        "config": str(config),
                        "version": LIBRARY_VERSION,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        if args.command == "configure-marktree":
            executable, config = configure_marktree_cli(args.cli, args.config)
            root = resolve_library_root(config_path=config)
            print(
                json.dumps(
                    {
                        "ok": True,
                        "action": "marktree-configured",
                        "library_root": str(root),
                        "marktree_cli": str(executable),
                        "config": str(config),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        root = resolve_library_root(args.root, args.config)
        layout = validate_library(root)
        if args.command == "show":
            config = _absolute(args.config or default_config_path())
            config_value = _json(config)
            print(
                json.dumps(
                    {
                        "ok": True,
                        "library_root": str(layout.root),
                        "home": str(layout.home),
                        "version": LIBRARY_VERSION,
                        "marktree_cli": config_value.get("marktree_cli"),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(f"私人知识库有效：{layout.root}")
        return 0
    except (LibraryError, OSError, UnicodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
