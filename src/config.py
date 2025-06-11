from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongodb_url: str = "mongodb://admin:password123@localhost:27017"
    db_name: str = "school_activities"

settings = Settings()
