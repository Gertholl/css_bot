import os
from sre_constants import LITERAL
from typing import Literal, Optional
from pydantic import BaseModel, Field


class Settings(BaseModel):
    API_TOKEN: Optional[Optional[str]] = Field(None, env="API_TOKEN")
    WEBHOOK_HOST: Optional[str] = Field(None, env="WEBHOOK_HOST")
    WEBHOOK_PATH: Optional[str] = Field(None, env="WEBHOOK_PATH")
    WEBHOOK_PORT: Optional[str] = Field(None, env="WEBHOOK_PORT")
    REDIS_URL: Optional[str] = Field(None, env="REDIS_URL")
    UPLOAD_DIR: Optional[str] = Field(None, env="UPLOAD_DIR")
    RESULT_FOLDER: Optional[str] = Field(None, env="RESULT_FOLDER")
    WEBSERVER_HOST: Optional[str] = Field(None, env="WEBSERVER_HOST")
    WEBSERVER_PORT: Optional[Optional[int]] = Field(None, env="WEBSERVER_PORT")
    CERTS_PATH: Optional[str] = Field(None, env="CERTS_PATH")
    SECRET_TOKEN: Optional[str] = Field(None, env="SECRET_TOKEN")
    MODE: Literal["dev", "prod"] = Field("dev", env="MODE")
