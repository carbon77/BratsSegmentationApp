from pydantic import BaseModel

class PatchScanRequest(BaseModel):
    title: str