#!/usr/bin/env python3
"""
感染症ダッシュボード バックエンドAPI
FastAPIを使用したRESTful API
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, date
from pydantic import BaseModel
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="感染症ダッシュボード API",
    description="東京都感染症データ分析・可視化API",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# データファイルのパス
DATA_DIR = "processed_data"
MAIN_DATA_FILE = os.path.join(DATA_DIR, "infectious_diseases_data.csv")
SUMMARY_FILE = os.path.join(DATA_DIR, "summary_statistics.json")
DISEASE_LIST_FILE = os.path.join(DATA_DIR, "disease_list.json")

# グローバルデータ変数
main_data: Optional[pd.DataFrame] = None
summary_stats: Optional[Dict] = None
disease_list: Optional[List[str]] = None

# Pydanticモデル
class DiseaseData(BaseModel):
    disease_name: str
    count: int
    year: int
    week: int
    report_date: str
    category: str

class TimeSeriesData(BaseModel):
    date: str
    value: int

class DiseaseTimeSeriesResponse(BaseModel):
    disease_name: str
    data: List[TimeSeriesData]

class SummaryResponse(BaseModel):
    total_records: int
    date_range: Dict[str, str]
    years_covered: List[int]
    total_diseases: int
    disease_categories: Dict[str, int]
    top_diseases: Dict[str, int]
    yearly_totals: Dict[str, int]

def load_data():
    """データファイルを読み込み"""
    global main_data, summary_stats, disease_list
    
    try:
        if os.path.exists(MAIN_DATA_FILE):
            main_data = pd.read_csv(MAIN_DATA_FILE)
            main_data['report_date'] = pd.to_datetime(main_data['report_date'])
            logger.info(f"メインデータを読み込みました: {len(main_data)} レコード")
        else:
            logger.warning(f"メインデータファイルが見つかりません: {MAIN_DATA_FILE}")
            main_data = pd.DataFrame()
        
        if os.path.exists(SUMMARY_FILE):
            with open(SUMMARY_FILE, 'r', encoding='utf-8') as f:
                summary_stats = json.load(f)
            logger.info("サマリー統計を読み込みました")
        else:
            logger.warning(f"サマリーファイルが見つかりません: {SUMMARY_FILE}")
            summary_stats = {}
        
        if os.path.exists(DISEASE_LIST_FILE):
            with open(DISEASE_LIST_FILE, 'r', encoding='utf-8') as f:
                disease_list = json.load(f)
            logger.info(f"疾病リストを読み込みました: {len(disease_list)} 疾病")
        else:
            logger.warning(f"疾病リストファイルが見つかりません: {DISEASE_LIST_FILE}")
            disease_list = []
            
    except Exception as e:
        logger.error(f"データ読み込みエラー: {str(e)}")
        main_data = pd.DataFrame()
        summary_stats = {}
        disease_list = []

@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    logger.info("アプリケーションを開始しています...")
    load_data()

@app.get("/")
async def root():
    """APIルートエンドポイント"""
    return {"message": "感染症ダッシュボード API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "healthy",
        "data_loaded": main_data is not None and not main_data.empty,
        "records_count": len(main_data) if main_data is not None else 0,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/summary", response_model=SummaryResponse)
async def get_summary():
    """サマリー統計を取得"""
    if not summary_stats:
        raise HTTPException(status_code=404, detail="サマリーデータが見つかりません")
    
    return SummaryResponse(**summary_stats)

@app.get("/diseases")
async def get_diseases():
    """疾病リストを取得"""
    if not disease_list:
        raise HTTPException(status_code=404, detail="疾病リストが見つかりません")
    
    return {"diseases": disease_list}

@app.get("/diseases/{disease_name}/timeseries")
async def get_disease_timeseries(
    disease_name: str,
    start_year: Optional[int] = Query(None, description="開始年"),
    end_year: Optional[int] = Query(None, description="終了年")
):
    """特定疾病の時系列データを取得"""
    if main_data is None or main_data.empty:
        raise HTTPException(status_code=404, detail="データが見つかりません")
    
    # 疾病名でフィルタリング
    disease_data = main_data[main_data['disease_name'] == disease_name].copy()
    
    if disease_data.empty:
        raise HTTPException(status_code=404, detail=f"疾病 '{disease_name}' のデータが見つかりません")
    
    # 年範囲でフィルタリング
    if start_year:
        disease_data = disease_data[disease_data['year'] >= start_year]
    if end_year:
        disease_data = disease_data[disease_data['year'] <= end_year]
    
    if disease_data.empty:
        raise HTTPException(status_code=404, detail="指定された条件のデータが見つかりません")
    
    # 日付でソート
    disease_data = disease_data.sort_values('report_date')
    
    # 時系列データを作成
    timeseries_data = []
    for _, row in disease_data.iterrows():
        timeseries_data.append({
            "date": row['report_date'].strftime('%Y-%m-%d'),
            "value": row['count']
        })
    
    return {
        "disease_name": disease_name,
        "data": timeseries_data,
        "total_records": len(timeseries_data)
    }

@app.get("/diseases/top")
async def get_top_diseases(
    limit: int = Query(10, description="取得件数"),
    year: Optional[int] = Query(None, description="対象年")
):
    """報告数上位の疾病を取得"""
    if main_data is None or main_data.empty:
        raise HTTPException(status_code=404, detail="データが見つかりません")
    
    data = main_data.copy()
    
    # 年でフィルタリング
    if year:
        data = data[data['year'] == year]
        if data.empty:
            raise HTTPException(status_code=404, detail=f"{year}年のデータが見つかりません")
    
    # 疾病別合計を計算
    top_diseases = data.groupby('disease_name')['count'].sum().sort_values(ascending=False).head(limit)
    
    result = []
    for disease, count in top_diseases.items():
        result.append({
            "disease_name": disease,
            "total_count": int(count),
            "category": data[data['disease_name'] == disease]['category'].iloc[0]
        })
    
    return {
        "top_diseases": result,
        "year": year,
        "total_diseases": len(result)
    }

@app.get("/categories")
async def get_categories():
    """感染症分類別統計を取得"""
    if main_data is None or main_data.empty:
        raise HTTPException(status_code=404, detail="データが見つかりません")
    
    category_stats = main_data.groupby('category').agg({
        'count': 'sum',
        'disease_name': 'nunique'
    }).round().astype(int)
    
    result = []
    for category, stats in category_stats.iterrows():
        result.append({
            "category": category,
            "total_count": stats['count'],
            "disease_count": stats['disease_name']
        })
    
    return {"categories": result}

@app.get("/yearly-trends")
async def get_yearly_trends():
    """年別感染症発生動向を取得"""
    if main_data is None or main_data.empty:
        raise HTTPException(status_code=404, detail="データが見つかりません")
    
    yearly_data = main_data.groupby('year')['count'].sum().sort_index()
    
    result = []
    for year, count in yearly_data.items():
        result.append({
            "year": int(year),
            "total_count": int(count)
        })
    
    return {"yearly_trends": result}

@app.get("/reload-data")
async def reload_data():
    """データの再読み込み"""
    try:
        load_data()
        return {
            "message": "データを再読み込みしました",
            "records_count": len(main_data) if main_data is not None else 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"データ再読み込みエラー: {str(e)}")
        raise HTTPException(status_code=500, detail="データの再読み込みに失敗しました")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)