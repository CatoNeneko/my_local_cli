"""启动本地工作台：python -m web。"""

import argparse


def main(argv=None):
    from cli import _version

    parser = argparse.ArgumentParser(description="本地 AI 开发工作台")
    parser.add_argument("--version", action="version", version="%(prog)s " + _version())
    parser.add_argument("--config", help="可信用户 TOML 配置文件")
    parser.add_argument("-C", "--workspace", help="服务允许的工作区根目录")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("端口必须在 1–65535 之间")
    from web.settings import Settings

    try:
        settings = Settings.from_env(config_path=args.config, workspace=args.workspace).validate()
    except ValueError as error:
        parser.error(str(error))
    import uvicorn
    from web.app import create_app

    # 无认证版本只监听 loopback；不提供误用的公网绑定开关。
    uvicorn.run(
        create_app(settings),
        host="127.0.0.1",
        port=args.port,
        workers=1,
        timeout_graceful_shutdown=3,
    )


if __name__ == "__main__":
    main()
