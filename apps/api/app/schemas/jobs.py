from pydantic import BaseModel, Field
from typing import Any, Literal
from datetime import datetime
JobStatus=Literal['queued','processing','completed','failed','expired']
class JobCreate(BaseModel): file_id:str; options:dict[str,Any]=Field(default_factory=dict)
class Job(BaseModel):
    id:str; status:JobStatus; tool_type:str; input_filename:str; output_filename:str|None=None; file_type:str|None=None; file_size:int=0; progress:int=0; current_step:str='queued'; report:dict[str,Any]=Field(default_factory=dict); download_token:str|None=None; expires_at:datetime|None=None; created_at:datetime; updated_at:datetime; error_message:str|None=None
