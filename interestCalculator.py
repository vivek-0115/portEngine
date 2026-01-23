from interestReport import generateInterestReport, buildBreakdown
from pydanticModel import InterestCalcPayload, ReportRequest
from fastapi.responses import StreamingResponse
from typing_extensions import Dict, Any
from fastapi import APIRouter, HTTPException
from datetime import datetime
from io import BytesIO
from uuid import uuid4

router = APIRouter(prefix='/api')

CALCULATIONS: Dict[str, Dict[str, Any]] = {}

def getInterest(ir, principal, duration):

    P = float(principal)
    R = float(ir) / 100

    years = int(duration.get("years", 0))
    months = int(duration.get("months", 0))
    days = int(duration.get("days", 0))

    interest_1_month = round(P * R, 2)
    interest_1_year = round(interest_1_month * 12, 2)
    interest_1_day = round(interest_1_month / 30, 2)

    interest_years = round(interest_1_year * years, 2)
    interest_months = round(interest_1_month * months, 2)
    interest_days = round(interest_1_day * days, 2)

    return interest_years + interest_months + interest_days

def getTotal(principal, interest):
    return principal + interest


@router.post("/calculate-interest")
def calculate_interest(payload: InterestCalcPayload):
    calculationId = str(uuid4())

    payload = payload.model_dump()

    CALCULATIONS[calculationId] = {
        "calculationId": calculationId,
        "createdAt": datetime.utcnow().isoformat() + "Z",
        "payload": payload,
    }

    P = payload.get('principal')
    D = payload.get('duration')

    return {
        "ok": True,
        "calculationId": calculationId,
        "interest_list": {
            'duration':payload.get('duration'),
            'details':[{
                'ir':ir,
                'principal': P,
                'interest': getInterest(ir, P, D),
                'total_payable': getTotal(P, getInterest(ir, P, D))
                } for ir in payload.get('rates')] 
        },
    }


@router.post("/interest-report")
def generateReport(req: ReportRequest):

    record = CALCULATIONS.get(req.calculationId)

    if not record:
        raise HTTPException(status_code=404, detail="Invalid calculationId or expired")

    payload = record["payload"]

    # Create final data for pdf generator
    pdf_data = {
        "type": "Simple Interest" if payload["type"] == "simple" else "Compound Interest",
        "generated": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "from_date": payload.get("from_date") or "",
        "to_date": payload.get("to_date") or "",
        "duration": payload["duration"],
        "principal": payload["principal"],
        "interest_rates": payload["rates"],
        "breakdown": buildBreakdown(payload)
    }

    pdf_bytes = generateInterestReport(pdf_data)

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=interestReport.pdf"}
    )