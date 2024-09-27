from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str

    PIXEL_IDS: list[int] = [1, 1000000]
    PAINT_REWARDS_POINT: list[int] = [5, 100, 200, 300, 500, 600]
    RECHARGE_SPEED_POINT: list[int] = [5, 100, 200, 300, 400, 500]
    ENERGY_LIMIT_POINT: list[int] = [5, 100, 200, 300, 400, 500]

    DELAY_ACCOUNT: list[int] = [0, 300]

    SLEEP: list[int] = [3600, 6000]
    SLEEP_BY_NIGHT: list[int] = [0, 6000]
    SLEEP_BY_NIGHT_ENABLE: bool = True

    USE_REF: bool = False
    REF_ID: str = ''
    START_PIXEL_X: int = 973
    START_PIXEL_Y: int = 901

    USE_PROXY_FROM_FILE: bool = False
    TASKS: list[str] = ["joinSquad", "x:notcoin", "x:notpixel"]
    BLUE: str = "#3690EA"
    WHITE: str = "#FFFFFF"
    BLACK: str = "#000000"
    RED: str = "#BE0039"
    YELLOW: str = "#FFD635"
    PINK: str = "#FF99AA"
    
settings = Settings()


