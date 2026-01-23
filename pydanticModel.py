from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class Duration(BaseModel):
    years: int = Field(0, ge=0)
    months: int = Field(0, ge=0)
    days: int = Field(0, ge=0)


class InterestCalcPayload(BaseModel):
    principal: float = Field(..., gt=0)
    rates: List[float] = Field(..., min_length=1, description="One or two interest rates in percent")

    type: Literal["simple", "compound"]

    compounding_frequency: Optional[int] = Field(
        default=None,
        description="Required only for compound interest (e.g. 1, 4, 12, 365)"
    )

    time_mode: Literal["calculate", "manual"]

    from_date: Optional[str] = None   # YYYY-MM-DD
    to_date: Optional[str] = None     # YYYY-MM-DD

    duration: Duration

class ReportRequest(BaseModel):
    calculationId: str
