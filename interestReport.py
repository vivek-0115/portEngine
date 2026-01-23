from reportlab.lib.pagesizes import A4
from datetime import datetime, date
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from io import BytesIO


def buildBreakdown(payload: dict) -> list[dict]:

    P = float(payload["principal"])
    rates = payload["rates"]

    duration = payload["duration"]
    years = int(duration.get("years", 0))
    months = int(duration.get("months", 0))
    days = int(duration.get("days", 0))

    breakdown = []

    for rate_percent in rates:
        R = float(rate_percent) / 100.0

        if payload["type"] == "simple":

            interest_1_month = round(P * R, 2)
            interest_1_year = round(interest_1_month * 12, 2)
            interest_1_day = round(interest_1_month / 30, 2)

            interest_years = round(interest_1_year * years, 2)
            interest_months = round(interest_1_month * months, 2)
            interest_days = round(interest_1_day * days, 2)

            total_interest = interest_years + interest_months + interest_days
            payable_amount = P + total_interest

            breakdown.append({
                "rate": rate_percent,

                "interest_1_day": interest_1_day,
                "interest_1_month": interest_1_month,
                "interest_1_year": interest_1_year,

                "years": years,
                "months": months,
                "days": days,

                "interest_years": interest_years,
                "interest_months": interest_months,
                "interest_days": interest_days,

                "total_interest": total_interest,
                "payable_amount": payable_amount
            })

    return breakdown




def generateInterestReport(payload: dict) -> bytes:
    """
    Generates a PDF summary report for interest calculation.
    Returns: PDF file as bytes (can be downloaded via FastAPI)
    """

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    LEFT = 25 * mm

    # --- Header ---
    c.setFont("Helvetica-Bold", 18)
    c.drawString(LEFT, height - 25 * mm, "Interest Calculation Report")

    interest_type = payload.get("type", "Simple Interest")
    generated = payload.get("generated") or datetime.now().strftime("%d %b %Y, %I:%M %p")

    c.setFont("Helvetica", 12)
    c.drawString(LEFT, height - 32 * mm, f"Type: {interest_type}")
    c.setFont("Helvetica", 11)
    c.drawString(LEFT, height - 37 * mm, f"Generated: {generated}")

    # Divider
    c.line(LEFT, height - 40 * mm, width - 25 * mm, height - 40 * mm)

    # --- Dates / Duration ---
    from_date = payload.get("from_date", "01/01/2022")
    to_date = payload.get("to_date", "01/01/2026")
    duration = payload.get("duration", {"years": 0, "months": 0, "days": 0})

    y = height - 50 * mm
    c.setFont("Helvetica", 13)
    c.drawString(LEFT, y, f"From: {from_date}, To: {to_date}")
    y -= 7 * mm
    c.setFont("Helvetica-Bold", 13)
    c.drawString(
        LEFT,
        y,
        f"Duration: {duration.get('years',0)} years, {duration.get('months',0)} months, {duration.get('days',0)} days"
    )

    # --- Principal ---
    principal = payload.get("principal", 0)
    y -= 10 * mm
    c.setFont("Helvetica", 14)
    c.drawString(LEFT, y, f"Principal Amount: {principal}")

    # --- Interest rate blocks (loop) ---
    y -= 10 * mm

    # breakdown list: we allow either:
    # - "breakdown" list already computed
    # - OR generate basic formula block with given interest_1_day etc (your case you can compute in backend)
    breakdown_list = payload.get("breakdown", [])
    if not breakdown_list:
        # fallback: create empty breakdown per rate
        for r in payload.get("interest_rates", []):
            breakdown_list.append({"rate": r})

    for item in breakdown_list:
        rate = item.get("rate", 0)

        # block title
        c.setFont("Helvetica", 15)
        c.drawString(LEFT, y, f"At {rate}% Interest Rate:")
        c.line(LEFT, y-8, width - 138 * mm, y-8)
        y -= 8 * mm

        # Pull values (default 0)
        i_day = item.get("interest_1_day", 0)
        i_month = item.get("interest_1_month", 0)
        i_year = item.get("interest_1_year", 0)

        days = item.get("days", duration.get("days", 0))
        months = item.get("months", duration.get("months", 0))
        years = item.get("years", duration.get("years", 0))

        i_days = item.get("interest_days", 0)
        i_months = item.get("interest_months", 0)
        i_years = item.get("interest_years", 0)

        total_interest = item.get("total_interest", (i_days + i_months + i_years))
        payable = item.get("payable_amount", (principal + total_interest))

        # lines (match sample style)
        c.setFont("Helvetica", 14)
        y -= 5 * mm

        c.drawString(LEFT, y, f"      Interest of 1 day:- {i_day}")
        y -= 7 * mm

        c.drawString(LEFT, y, f"      Interest of 1 Month:- {i_day} x 30 = {i_month}")
        y -= 7 * mm

        c.drawString(LEFT, y, f"      Interest of 1 Year:- {i_month} x 12 = {i_year}")
        y -= 7 * mm

        y -= 5 * mm

        c.drawString(LEFT, y, f"      Interest of {days} Days:- {i_day} x {days} = {i_days}")
        y -= 7 * mm

        c.drawString(LEFT, y, f"      Interest of {months} Months:- {i_month} x {months} = {i_months}")
        y -= 7 * mm

        c.drawString(LEFT, y, f"      Interest of {years} Years:- {i_year} x {years} = {i_years}")
        y -= 7 * mm

        y -= 5 * mm

        c.drawString(LEFT, y, f"      Total Interest:- {i_days} + {i_months} + {i_years} = {total_interest}")
        y -= 7 * mm

        y -= 5 * mm

        c.setFont("Helvetica-Bold", 14)
        c.drawString(LEFT, y, f"      Payable Amount:- {principal} + {total_interest} = {payable}")
        y -= 12 * mm

        # new page safety
        if y < 30 * mm:
            c.showPage()
            y = height - 25 * mm

    # Footer
    footer_y = 15 * mm

    # Part 1
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(colors.black)
    c.drawString(LEFT, footer_y, "Generated by portEngine • ")

    # Measure width of first part
    part1 = "Generated by portEngine • "
    w1 = c.stringWidth(part1, "Helvetica", 10)

    # Part 2 (clickable link)
    link_text = "BytesCode(Vivek)"
    link_url = "https://vivek0115.vercel.app/"

    x_link = LEFT + w1

    # Make link blue
    c.setFillColor(colors.blue)
    c.drawString(x_link, footer_y, link_text)

    # underline link
    w2 = c.stringWidth(link_text, "Helvetica", 10)
    c.setLineWidth(0.6)
    c.setStrokeColor(colors.blue)
    c.line(x_link, footer_y - 1, x_link + w2, footer_y - 1)

    # clickable region
    c.linkURL(
        link_url,
        (x_link, footer_y - 2, x_link + w2, footer_y + 10),
        relative=0
    )

    # Part 3
    part3 = " • Interest Calculator Tool"
    x3 = x_link + w2

    c.setFillColor(colors.black)
    c.drawString(x3, footer_y, part3)

    # Reset defaults (optional good practice)
    c.setStrokeColor(colors.black)
    c.setFillColor(colors.black)

    c.showPage()
    c.save()

    pdf = buf.getvalue()
    buf.close()
    return pdf

