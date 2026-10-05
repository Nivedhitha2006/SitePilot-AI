from pydantic import BaseModel,HttpUrl,Field
class AnalyzeRequest(BaseModel): url:HttpUrl; max_pages:int=Field(default=25,ge=1,le=100)
