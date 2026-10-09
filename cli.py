"""命令行启动入口；先解析参数，因此 --help 不连接模型或启动 MCP。"""
import argparse
from pathlib import Path


def build_parser():
    parser = argparse.ArgumentParser(prog="ai-cli", description="本地 AI 编程助手（开发中）")
    parser.add_argument("--approval-mode", choices=("auto", "manual"), default="auto", help="auto 自动审批低风险操作，manual 保留逐次确认")
    parser.add_argument("--provider", choices=("ollama", "openai"), help="模型协议")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY", help="保存 API 密钥的环境变量名；不保存密钥")
    parser.add_argument("--model", help="覆盖配置中的模型名称")
    parser.add_argument("--base-url", help="覆盖模型服务地址")
    parser.add_argument("--session", help="启动时进入指定会话，不存在则创建")
    parser.add_argument("--plain", action="store_true", help="使用普通 input，关闭增强终端编辑")
    parser.add_argument("--no-mcp", action="store_true", help="本次运行不启动 MCP 服务")
    parser.add_argument('-C', '--workspace', default=str(Path.cwd()), help='工作目录，默认当前目录')
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    from config import model_config, approval_config
    from script import main as run_cli
    approval_config["mode"] = args.approval_mode
    if args.provider:
        model_config["provider"] = args.provider
    model_config["api_key_env"] = args.api_key_env
    if args.model:
        model_config["model"] = args.model
    if args.base_url:
        model_config["base_url"] = args.base_url.rstrip("/")
    try:
        run_cli(initial_session=args.session, plain=args.plain, no_mcp=args.no_mcp, workspace=args.workspace)
    except ValueError as error:
        parser.error(str(error))
    except (EOFError, KeyboardInterrupt):
        print("\nCLI 已退出")


if __name__ == "__main__":
    main()
