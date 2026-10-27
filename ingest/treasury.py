"""US Treasury Monthly Treasury Statement table 4: Customs Duties receipts (gross, refunds, net). No key."""
import pandas as pd

from .common import http_get, record, save

URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/mts/mts_table_4"


def run(start: str = "2015-01-01"):
    rows, page = [], 1
    while True:
        params = {"filter": f"classification_desc:eq:Customs Duties,record_date:gte:{start}",
                  "sort": "record_date", "page[size]": 500, "page[number]": page}
        js = http_get(URL, params=params).json()
        rows += js["data"]
        if page >= js["meta"]["total-pages"]:
            break
        page += 1
    df = pd.DataFrame(rows)
    keep = ["record_date", "classification_desc", "current_month_gross_rcpt_amt", "current_month_refund_amt",
            "current_month_net_rcpt_amt", "current_fytd_net_rcpt_amt", "record_fiscal_year", "record_calendar_month"]
    df = df[[c for c in keep if c in df.columns]].copy()
    for c in df.columns:
        if c.endswith("_amt"):
            df[c] = pd.to_numeric(df[c].replace("null", None), errors="coerce")
    df["record_date"] = pd.to_datetime(df["record_date"])
    df = df.drop_duplicates(["record_date"])
    save(df, "treasury", "mts_customs_duties_monthly")
    return record("treasury", "mts_customs_duties_monthly", df, url=URL, date_col="record_date")
