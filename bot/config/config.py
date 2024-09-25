from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str

    PIXEL_IDS: list[int] = [1, 1000000]
    PAINT_REWARDS_POINT: list[int] = [5, 100, 200, 300, 500]
    RECHARGE_SPEED_POINT: list[int] = [5, 100, 200, 300, 500]
    ENERGY_LIMIT_POINT: list[int] = [5, 100, 200, 300, 500]

    DELAY_ACCOUNT: list[int] = [0, 300]

    SLEEP: list[int] = [3600, 7200]
    SLEEP_BY_NIGHT: list[int] = [0, 7200]
    SLEEP_BY_NIGHT_ENABLE: bool = True

    USE_REF: bool = False
    REF_ID: str = ''

    USE_PROXY_FROM_FILE: bool = False
    TASKS: list[str] = ["joinSquad", "joinSquad", "x:notcoin", "x:notpixel"]
    COLORS: list[str] = ["#7EED56", "#000000", "#FFFFFF", "#898D90", "#51E9F4"]

settings = Settings()


