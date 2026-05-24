from pydantic import BaseModel
class UploadResponse(BaseModel): file_id:str; filename:str; file_size:int; content_type:str|None=None
