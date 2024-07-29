import os
from dataclasses import dataclass


@dataclass(frozen=False)
class Config:

    API_TOKEN: str = os.getenv("API_TOKEN")
    WEBHOOK_HOST: str = os.getenv("WEBHOOK_HOST")
    WEBHOOK_PATH: str = os.getenv("WEBHOOK_PATH", "/webhook")
    WEBHOOK_PORT: int = os.getenv("WEBHOOK_PORT", None)
    REDIS_URL: str = os.getenv("REDIS_URL")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR")
    RESULT_FOLDER: str = os.getenv("RESULT_FOLDER")
    WEBSERVER_HOST: str = os.getenv("WEBSERVER_HOST")
    WEBSERVER_PORT: int = int(os.getenv("WEBSERVER_PORT"))
    SECRET_TOKEN: str = os.getenv("SECRET_TOKEN")

    def __post_init__(self):
        if self.API_TOKEN is None:
            raise ValueError("API_TOKEN is not set")
        if not self.WEBHOOK_PATH.startswith("/") and self.WEBHOOK_HOST is not None:
            raise ValueError("WEBHOOK_PATH must start with '/' or be empty")
        if self.WEBHOOK_HOST is None:
            raise ValueError("WEBHOOK_HOST is not set")
        if self.REDIS_URL is None:
            raise ValueError("REDIS_URL is not set")
        if self.UPLOAD_DIR is None:
            raise ValueError("UPLOAD_DIR is not set")
        if self.RESULT_FOLDER is None:
            raise ValueError("RESULT_FOLDER is not set")
        if self.WEBSERVER_HOST is None:
            raise ValueError("WEBSERVER_HOST is not set")
        if self.WEBSERVER_PORT is None:
            raise ValueError("WEBSERVER_PORT is not set")

        if self.WEBHOOK_PORT is None:
            self.WEBHOOK_PATH = "/".join([self.WEBHOOK_HOST, "webhook", self.API_TOKEN])
        else:
            self.WEBHOOK_PATH = "/".join(
                [
                    self.WEBHOOK_HOST + ":" + str(self.WEBHOOK_PORT),
                    "webhook",
                    self.API_TOKEN,
                ]
            )
