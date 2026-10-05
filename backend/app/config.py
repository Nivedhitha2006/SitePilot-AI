from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    database_url:str='sqlite:///./website_optimizer.db'; pagespeed_api_key:str=''; llm_api_key:str=''; llm_base_url:str=''; llm_model:str=''; max_crawl_pages:int=25; request_timeout:int=10; upload_max_mb:int=10
    model_config=SettingsConfigDict(env_file='.env', extra='ignore')
settings=Settings()
