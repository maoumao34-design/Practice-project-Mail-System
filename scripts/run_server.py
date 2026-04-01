import uvicorn

from server.config import get_settings


if __name__ == "__main__":
    settings = get_settings()
    # 生产环境勿开启热重载，且勿长期用本脚本对外暴露
    use_reload = settings.app_env != "production"
    uvicorn.run(
        "server.main:app",
        host="127.0.0.1",
        port=8000,
        reload=use_reload,
    )
