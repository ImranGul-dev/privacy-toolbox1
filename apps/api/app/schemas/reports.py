from pydantic import BaseModel
class ScanReport(BaseModel): risk_score:int; summary:str; categories:list[str]; findings:list[dict]; warnings:list[str]=[]; limitations:list[str]=[]
