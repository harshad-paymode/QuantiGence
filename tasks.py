import os
import pandas as pd
import numpy as np
from celery import Celery
from dotenv import load_dotenv

# Import your existing core logic
from src.core.constants import RATIO_GROUPS
from src.services.risk_matrix import calculate_category_scores
from src.orchestration.graph import run_pipeline

load_dotenv()

# Initialize Celery app
celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

AZURE_BASE = "az://data"

def _read_parquet(path: str) -> pd.DataFrame:
    try:
        df = pd.read_parquet(
            path,
            storage_options={
                "connection_string": os.getenv("AZURE_STORAGE_CONNECTION_STRING")
            }
        )
        return df
    except Exception as e:
        print(f"AZURE ERROR: {e}")
        raise

@celery_app.task(name="fetch_charts_task")
def fetch_charts_task(company: str, variables: list, timeframe: str):
    blob_path = f"{AZURE_BASE}/stocks/{timeframe}/{timeframe}.parquet"
    df = _read_parquet(blob_path)

    if isinstance(df.index, pd.PeriodIndex):
        df.index = df.index.to_timestamp()

    selected = [(var, company) for var in variables if (var, company) in df.columns]
    if not selected:
        return []

    out = df[selected].copy()
    out.columns = [col[0] for col in selected]
    out["date"] = df.index.astype(str) # Convert to string for JSON serialization
    out = out.replace([np.inf, -np.inf, np.nan], None).sort_index()

    return out.reset_index(drop=True).to_dict(orient="records")

@celery_app.task(name="fetch_ratios_task")
def fetch_ratios_task(company: str, timeframe: str, variables: list):
    blob_path = f"{AZURE_BASE}/ratios/{timeframe}/all_ratios.parquet"
    df = _read_parquet(blob_path)

    if not isinstance(df.index, pd.MultiIndex):
        raise ValueError("Expected MultiIndex index in ratios parquet")

    df_company = df.xs(company, level=0)
    if variables:
        df_company = df_company.reindex(variables)

    df_company.columns = df_company.columns.to_period().astype(str)
    df_company = df_company.replace([np.inf, -np.inf, np.nan], None)

    return df_company.reset_index().to_dict(orient='records')

@celery_app.task(name="fetch_performance_task")
def fetch_performance_task(company: str, period: str, timeframe: str):
    blob_path = f"{AZURE_BASE}/metrics/{timeframe}/all_metrics.parquet"
    df = _read_parquet(blob_path)

    if not isinstance(df.columns, pd.MultiIndex):
        return {}
    
    df_company = df.xs(company, level=1, axis=1)
    period_fmt = period[3:] + period[:2]
    df_company_period = df_company[df_company.index == period_fmt]
    df_company_period.index = df_company_period.index.astype(str)
    df_company_period = df_company_period.replace([np.inf, -np.inf, np.nan], None)

    return df_company_period.reset_index().to_dict(orient='records')

@celery_app.task(name="fetch_risk_matrix_task")
def fetch_risk_matrix_task(company: str, period: str, timeframe: str, top_n: str):
    blob_path = f"{AZURE_BASE}/ratios/{timeframe}/all_ratios.parquet"
    df = _read_parquet(blob_path)

    if not isinstance(df.index, pd.MultiIndex):
        return {}
    
    df.columns = df.columns.to_period().astype(str)
    period_fmt = period[3:] + period[:2]
    df_company = df.xs(company, level=0, axis=0)
    df_company_period = df_company.loc[:, period_fmt]

    result = calculate_category_scores(df_company_period, RATIO_GROUPS)
    return result["category_scores"]

@celery_app.task(name="fetch_qualitative_task")
def fetch_qualitative_task(company: str, period: str, query: str):
    user_query = f"Company: {company}, Period: {period}, Query: {query}"

    # Use a static session ID for now, or pass dynamically
    result = run_pipeline(user_query, "e9bd98df-2cf5-4d53-92ad-a14bbbcb5e9e")

    # ENSURE JSON COMPATIBILITY
    # If your scores are numpy types, cast them to standard python floats
    faithfulness = float(result['audit_score']['faithfulness'])
    relevancy = float(result['audit_score']['answer_relevancy'])

    print("The scores are",faithfulness, relevancy)
    
    return {
        "final_response": str(result['final_response']),
        "audit_score": {
            "faithfulness": faithfulness,
            "answer_relevancy": relevancy
        }
    }