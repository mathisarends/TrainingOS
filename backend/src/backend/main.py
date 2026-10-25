import uvicorn

from backend.settings import AppSettings


def main() -> None:
    settings = AppSettings()
    # OAuth callback query strings contain credentials; do not write them to access logs.
    uvicorn.run("backend.app:app", host=settings.host, port=settings.port, access_log=False)


if __name__ == "__main__":
    main()
