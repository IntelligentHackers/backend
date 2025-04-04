from enum import Enum
import torch
from bson import ObjectId
from pydantic import BaseModel

class SelectionResult(str, Enum):
    approved = "approved"
    rejected = "rejected"

    @property
    def award(self):
        if self == self.approved:
            award = 1
        else:
            award = 0
        return torch.tensor([[award]], dtype=torch.float32)

class Selection(BaseModel):
    _id: ObjectId
    subject: str
    object: str
    result: SelectionResult
