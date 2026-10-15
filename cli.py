"""命令行启动入口；先解析参数，因此 --help 不连接模型或启动 MCP。"""

import argparse
from dataclasses import asdict
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import sys


def _version():
    try:
        return version("local-ai-cli")
    except PackageNotFoundError:
        return "0.2.0"


def build_parser():
    parser = argparse.ArgumentParser(prog="ai-cli", description="本地 AI 编程助手（开发中）")
    parser.add_argument("--version", action="version", version=f"%(prog)s {_version()}")
    parser.add_argument("--config", help="可信用户 TOML 配置文件路径")
    parser.add_argument("--doctor", action="store_true", help="离线检查运行环境，不请求模型")
    parser.add_argument("--show-config", action="store_true", help="显示合并后的配置，不读取密钥值")
    parser.add_argument("--json", action="store_true", help="诊断或配置使用 JSON 输出")
    parser.add_argument(
        "--approval-mode",
        choices=("auto", "manual"),
        default=None,
        help="auto 自动审批低风险操作，manual 人工审阅启动和文件修改",
    )
    parser.add_argument("--provider", choices=("ollama", "openai"), help="模型协议")
    parser.add_argument("--api-key-env", default=None, help="保存 API 密钥的环境变量名；不保存密钥")
    parser.add_argument("--model", help="覆盖配置中的模型名称")
    parser.add_argument("--base-url", help="覆盖模型服务地址")
    parser.add_argument("--session", help="启动时进入指定会话，不存在则创建")
    parser.add_argument("--plain", action="store_true", help="使用普通 input，关闭增强终端编辑")
    parser.add_argument(
        "--no-mcp", action="store_true", default=None, help="本次运行不启动 MCP 服务"
    )
    parser.add_argument("-C", "--workspace", default=str(Path.cwd()), help="工作目录，默认当前目录")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    from harness.configuration import load_configuration

    try:
        settings = load_configuration(
            args.config,
            overrides={
                "provider": args.provider,
                "model": args.model,
                "base_url": args.base_url,
                "api_key_env": args.api_key_env,
                "approval_mode": args.approval_mode,
                "mcp_enabled": False if args.no_mcp else None,
            },
        )
    except ValueError as error:
        parser.error(str(error))

    if args.doctor:
        from harness.diagnostics import doctor

        report = doctor(settings, args.workspace)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            for check in report["checks"]:
                print(f"[{check['status']}] {check['name']}: {check['message']}")
        return 0 if report["ok"] else 1
    if args.show_config:
        print(json.dumps(asdict(settings), ensure_ascii=False, indent=2))
        return 0
    if args.json:
        parser.error("--json 需要与 --doctor 或 --show-config 一起使用")
    if not settings.model:
        parser.error("请通过 --model、AI_CLI_MODEL 或用户配置 [model].name 配置模型")

    from config import model_config, approval_config

    approval_config["mode"] = settings.approval_mode
    model_config.update(settings.model_settings())
    from script import main as run_cli

    try:
        run_cli(
            initial_session=args.session,
            plain=args.plain,
            no_mcp=not settings.mcp_enabled,
            workspace=args.workspace,
        )
    except ValueError as error:
        parser.error(str(error))
    except (EOFError, KeyboardInterrupt):
        print("\nCLI 已退出")


if __name__ == "__main__":
    sys.exit(main())
