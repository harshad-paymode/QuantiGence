# from fastapi import FastAPI, HTTPException, Query, Request
# from fastapi.middleware.cors import CORSMiddleware
# from src.core.constants import RATIO_GROUPS
# from typing import List, Optional
# from src.services.risk_matrix import calculate_category_scores
# from src.orchestration.graph import run_pipeline
# from src.core.state import init_query_state
# import pandas as pd
# import numpy as np
# from dotenv import load_dotenv
# import os
# from pydantic import BaseModel # Import this


# load_dotenv()

# app = FastAPI(title="QuantiGence Backend")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# AZURE_BASE = "az://data"  # keep same path form; adjust if you read locally


# # 1. Define the schema for the incoming JSON
# class QualitativeRequest(BaseModel):
#     company: str
#     period: str
#     query: str = ""

# def _read_parquet(path: str) -> pd.DataFrame:
#     try:
#         print("Trying to read:", path)
#         print("Conn string exists?:", os.getenv("AZURE_STORAGE_CONNECTION_STRING") is not None)

#         df = pd.read_parquet(
#             path,
#             storage_options={
#                 "connection_string": os.getenv("AZURE_STORAGE_CONNECTION_STRING")
#             }
#         )
#         print("Read success")
       
#         return df
#     except Exception as e:
#         print("AZURE ERROR:")
#         raise


# @app.get("/api/charts")
# async def get_charts(company: str, variables: List[str] = Query(...), timeframe: str = "quarterly"):
#     try:
#         blob_path = f"{AZURE_BASE}/stocks/{timeframe}/{timeframe}.parquet"
#         df = _read_parquet(blob_path)

#         # Convert PeriodIndex → Timestamp (important for quarterly/monthly)
#         if isinstance(df.index, pd.PeriodIndex):
#             df.index = df.index.to_timestamp()

#         # Select exact MultiIndex columns
#         selected = [(var, company) for var in variables if (var, company) in df.columns]
#         if not selected:
#             return []

#         # Slice only required columns
#         out = df[selected].copy()

#         # Flatten column names (use first level only)
#         out.columns = [col[0] for col in selected]

#         # Use index directly as date
#         out["date"] = df.index

#         # Clean
#         out = out.replace([np.inf, -np.inf, np.nan], None)
#         out = out.sort_index()

#         print(out['date'])
#         return out.reset_index(drop=True).to_dict(orient="records")

#     except Exception as e:
#         print("REAL ERROR:", e)
#         raise HTTPException(status_code=500, detail=str(e))


# @app.get("/api/ratios")
# def get_ratios(
#     company: str = Query(...),
#     timeframe: str = Query("quarterly"),
#     variables: List[str] = Query(None),
# ):
#     try:
#         # path to parquet (adjust AZURE_BASE or BASE_PATH as in your file)
#         blob_path = f"{AZURE_BASE}/ratios/{timeframe}/all_ratios.parquet"
#         df = _read_parquet(blob_path)

#         # expect MultiIndex (company, metric)
#         if not isinstance(df.index, pd.MultiIndex):
#             raise HTTPException(status_code=500, detail="Expected MultiIndex index in ratios parquet")

#         # select company's block (index level 0 == company). This returns DataFrame indexed by metric names.
#         df_company = df.xs(company, level=0)

#         # if variables provided, reindex to that order (will produce NaN for missing metrics)
#         if variables:
#             df_company = df_company.reindex(variables)

#         df_company.columns = df_company.columns.to_period().astype(str)

#         df_company = df_company.replace([np.inf, -np.inf, np.nan], None)

#         return df_company.reset_index().to_dict(orient='records')
#     except Exception as e:
#         print("RATIOS ERROR:", repr(e))
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/api/performance")
# async def get_performance(company:str, period: str, timeframe: str = "quarterly"):
#     try:
#         blob_path = f"{AZURE_BASE}/metrics/{timeframe}/all_metrics.parquet"
#         df = _read_parquet(blob_path)

#         # expect MultiIndex (company, metric)
#         if not isinstance(df.columns, pd.MultiIndex):
#             return {}
        
#         df_company = df.xs(company, level=1, axis=1)

#         #refromat period according to the dataframe

#         period = period[3:] + period[:2]
    
#         df_company_period = df_company[df_company.index == period]

#         #reformat columns into strings to avoid comples data type
#         df_company_period.index = df_company_period.index.astype(str)

#         df_company_period = df_company_period.replace([np.inf, -np.inf, np.nan], None)

#         return df_company_period.reset_index().to_dict(orient='records')

#     except Exception as e:
#         print("PERFORMANCE ERROR:", repr(e))
#         raise HTTPException(status_code=500, detail=str(e))
    
# @app.get("/api/risk_matrix")
# async def get_risk_matrix(company:str, period: str, timeframe: str = "quarterly", top_n: str = "5"):
#     try:
#         blob_path = f"{AZURE_BASE}/ratios/{timeframe}/all_ratios.parquet"
#         df = _read_parquet(blob_path)

#         # expect MultiIndex (company, metric)
#         if not isinstance(df.index, pd.MultiIndex):
#             return {}
        
#         df.columns = df.columns.to_period().astype(str)

#         #refromat period according to the dataframe

#         period = period[3:] + period[:2]

#         df_company = df.xs(company,level=0,axis=0)

#         df_company_period = df_company.loc[:,period]

#         result = calculate_category_scores(df_company_period, RATIO_GROUPS)

#         return result["category_scores"]

#     except Exception as e:
#         print("RISK MATRIX:", repr(e))
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/api/qualitative")
# # 2. Use the model as the argument
# async def get_qualitative_analysis(req: QualitativeRequest):
#     try:
#         # 3. Access data using req.field_name
#         user_query = f"Company: {req.company}, Period: {req.period}, Query: {req.query}"
        
#         result = run_pipeline(user_query, "e9bd98df-2cf5-4d53-92ad-a14bbbcb5e9e")
        
#         print(result)
#         return result
#     except Exception as e:
#         print("QUALITATIVE ERROR:", repr(e))
#         raise HTTPException(status_code=500, detail=str(e))


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from celery.result import AsyncResult

# Import the celery instance and tasks
from tasks import (
    celery_app, fetch_charts_task, fetch_ratios_task, 
    fetch_performance_task, fetch_risk_matrix_task, fetch_qualitative_task
)

app = FastAPI(title="QuantiGence Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QualitativeRequest(BaseModel):
    company: str
    period: str
    query: str = ""

# --- TASK POLLING ENDPOINT ---
@app.get("/api/task-status/{task_id}")
async def get_task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    
    if task_result.state == "PENDING" or task_result.state == "STARTED":
        return {"status": "processing"}
    elif task_result.state == "SUCCESS":
        return {"status": "completed", "data": task_result.result}
    elif task_result.state == "FAILURE":
        return {"status": "failed", "error": str(task_result.info)}
    
    return {"status": task_result.state}

# --- ASYNC API ENDPOINTS ---
@app.get("/api/charts")
async def get_charts(company: str, variables: List[str] = Query(...), timeframe: str = "quarterly"):
    task = fetch_charts_task.delay(company, variables, timeframe)
    return {"task_id": task.id}

@app.get("/api/ratios")
def get_ratios(company: str = Query(...), timeframe: str = Query("quarterly"), variables: List[str] = Query(None)):
    task = fetch_ratios_task.delay(company, timeframe, variables or [])
    return {"task_id": task.id}

@app.get("/api/performance")
async def get_performance(company: str, period: str, timeframe: str = "quarterly"):
    task = fetch_performance_task.delay(company, period, timeframe)
    return {"task_id": task.id}
    
@app.get("/api/risk_matrix")
async def get_risk_matrix(company: str, period: str, timeframe: str = "quarterly", top_n: str = "5"):
    task = fetch_risk_matrix_task.delay(company, period, timeframe, top_n)
    return {"task_id": task.id}

@app.post("/api/qualitative")
async def get_qualitative_analysis(req: QualitativeRequest):
    task = fetch_qualitative_task.delay(req.company, req.period, req.query)
    return {"task_id": task.id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)