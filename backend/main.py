#!/usr/bin/env python3
"""
感染症ダッシュボード バックエンドAPI
FastAPIを使用したRESTful API
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
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

# データ更新モジュールをインポート
try:
    from data_updater import DataUpdater
    DATA_UPDATER_AVAILABLE = True
except ImportError:
    DATA_UPDATER_AVAILABLE = False
    logger.warning("data_updaterモジュールが利用できません")

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

# 定点把握疾患データファイルのパス
# バックエンドディレクトリから見た相対パス
SENTINEL_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
SENTINEL_DATA_FILE = os.path.join(SENTINEL_DATA_DIR, "sentinel_diseases_data.csv")
SENTINEL_SUMMARY_FILE = os.path.join(SENTINEL_DATA_DIR, "sentinel_summary_statistics.json")
SENTINEL_DISEASE_LIST_FILE = os.path.join(SENTINEL_DATA_DIR, "sentinel_disease_list.json")

# グローバルデータ変数
main_data: Optional[pd.DataFrame] = None
summary_stats: Optional[Dict] = None
disease_list: Optional[List[str]] = None
sentinel_data: Optional[pd.DataFrame] = None
sentinel_summary_stats: Optional[Dict] = None
sentinel_disease_list: Optional[List[str]] = None

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
    global main_data, summary_stats, disease_list, sentinel_data, sentinel_summary_stats, sentinel_disease_list
    
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
        
        # 定点把握疾患データの読み込み
        if os.path.exists(SENTINEL_DATA_FILE):
            sentinel_data = pd.read_csv(SENTINEL_DATA_FILE)
            logger.info(f"定点把握疾患データを読み込みました: {len(sentinel_data)} レコード")
        else:
            logger.warning(f"定点把握疾患データファイルが見つかりません: {SENTINEL_DATA_FILE}")
            sentinel_data = pd.DataFrame()
        
        if os.path.exists(SENTINEL_SUMMARY_FILE):
            with open(SENTINEL_SUMMARY_FILE, 'r', encoding='utf-8') as f:
                sentinel_summary_stats = json.load(f)
            logger.info("定点把握疾患サマリー統計を読み込みました")
        else:
            logger.warning(f"定点把握疾患サマリーファイルが見つかりません: {SENTINEL_SUMMARY_FILE}")
            sentinel_summary_stats = {}
        
        if os.path.exists(SENTINEL_DISEASE_LIST_FILE):
            with open(SENTINEL_DISEASE_LIST_FILE, 'r', encoding='utf-8') as f:
                sentinel_disease_list = json.load(f)
            logger.info(f"定点把握疾患リストを読み込みました: {len(sentinel_disease_list)} 疾病")
        else:
            logger.warning(f"定点把握疾患リストファイルが見つかりません: {SENTINEL_DISEASE_LIST_FILE}")
            sentinel_disease_list = []
            
    except Exception as e:
        logger.error(f"データ読み込みエラー: {str(e)}")
        main_data = pd.DataFrame()
        summary_stats = {}
        disease_list = []
        sentinel_data = pd.DataFrame()
        sentinel_summary_stats = {}
        sentinel_disease_list = []

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
async def get_summary(
    start_year: Optional[int] = Query(None, description="開始年"),
    end_year: Optional[int] = Query(None, description="終了年")
):
    """サマリー統計を取得"""
    if not summary_stats:
        raise HTTPException(status_code=404, detail="サマリーデータが見つかりません")
    
    if start_year is None and end_year is None:
        return SummaryResponse(**summary_stats)
    
    # 期間フィルタリングが指定された場合、データを再計算
    if main_data is None or main_data.empty:
        raise HTTPException(status_code=404, detail="データが見つかりません")
    
    filtered_data = main_data.copy()
    
    if start_year:
        filtered_data = filtered_data[filtered_data['year'] >= start_year]
    if end_year:
        filtered_data = filtered_data[filtered_data['year'] <= end_year]
    
    if filtered_data.empty:
        raise HTTPException(status_code=404, detail="指定された条件のデータが見つかりません")
    
    # フィルタリングされたデータで統計を再計算
    total_records = len(filtered_data)
    years_covered = sorted(filtered_data['year'].unique().tolist())
    total_diseases = filtered_data['disease_name'].nunique()
    
    disease_categories = filtered_data.groupby('category')['count'].sum().to_dict()
    top_diseases = filtered_data.groupby('disease_name')['count'].sum().sort_values(ascending=False).head(10).to_dict()
    yearly_totals = filtered_data.groupby('year')['count'].sum().to_dict()
    
    # yearly_totalsのキーを文字列に変換
    yearly_totals = {str(year): count for year, count in yearly_totals.items()}
    
    date_range = {
        "start": filtered_data['report_date'].min().strftime('%Y-%m-%d'),
        "end": filtered_data['report_date'].max().strftime('%Y-%m-%d')
    }
    
    return SummaryResponse(
        total_records=total_records,
        date_range=date_range,
        years_covered=years_covered,
        total_diseases=total_diseases,
        disease_categories=disease_categories,
        top_diseases=top_diseases,
        yearly_totals=yearly_totals
    )

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
    year: Optional[int] = Query(None, description="対象年"),
    start_year: Optional[int] = Query(None, description="開始年"),
    end_year: Optional[int] = Query(None, description="終了年")
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
    
    # 期間フィルタリング
    if start_year:
        data = data[data['year'] >= start_year]
    if end_year:
        data = data[data['year'] <= end_year]
    
    if data.empty:
        raise HTTPException(status_code=404, detail="指定された条件のデータが見つかりません")
    
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
async def get_categories(
    start_year: Optional[int] = Query(None, description="開始年"),
    end_year: Optional[int] = Query(None, description="終了年")
):
    """感染症分類別統計を取得"""
    if main_data is None or main_data.empty:
        raise HTTPException(status_code=404, detail="データが見つかりません")
    
    data = main_data.copy()
    
    # 期間フィルタリング
    if start_year:
        data = data[data['year'] >= start_year]
    if end_year:
        data = data[data['year'] <= end_year]
    
    if data.empty:
        raise HTTPException(status_code=404, detail="指定された条件のデータが見つかりません")
    
    category_stats = data.groupby('category').agg({
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
async def get_yearly_trends(
    start_year: Optional[int] = Query(None, description="開始年"),
    end_year: Optional[int] = Query(None, description="終了年")
):
    """年別感染症発生動向を取得"""
    if main_data is None or main_data.empty:
        raise HTTPException(status_code=404, detail="データが見つかりません")
    
    data = main_data.copy()
    
    # 期間フィルタリング
    if start_year:
        data = data[data['year'] >= start_year]
    if end_year:
        data = data[data['year'] <= end_year]
    
    if data.empty:
        raise HTTPException(status_code=404, detail="指定された条件のデータが見つかりません")
    
    yearly_data = data.groupby('year')['count'].sum().sort_index()
    
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

@app.get("/update-status")
async def get_update_status():
    """データ更新状態を取得"""
    if not DATA_UPDATER_AVAILABLE:
        raise HTTPException(status_code=503, detail="データ更新機能が利用できません")
    
    try:
        updater = DataUpdater()
        status = updater.get_update_status()
        return status
    except Exception as e:
        logger.error(f"更新状態取得エラー: {str(e)}")
        raise HTTPException(status_code=500, detail="更新状態の取得に失敗しました")

@app.post("/update-data")
async def update_data(background_tasks: BackgroundTasks, force: bool = Query(False, description="強制再処理")):
    """データを更新（バックグラウンド処理）"""
    if not DATA_UPDATER_AVAILABLE:
        raise HTTPException(status_code=503, detail="データ更新機能が利用できません")
    
    def run_update():
        """バックグラウンドでデータ更新を実行"""
        try:
            updater = DataUpdater()
            result = updater.update_data(force_reprocess=force)
            logger.info(f"データ更新完了: {result}")
            
            # 更新後、データを再読み込み
            load_data()
        except Exception as e:
            logger.error(f"バックグラウンド更新エラー: {str(e)}")
    
    # バックグラウンドタスクとして実行
    background_tasks.add_task(run_update)
    
    return {
        "message": "データ更新を開始しました",
        "timestamp": datetime.now().isoformat(),
        "force": force
    }

@app.post("/update-data-sync")
async def update_data_sync(force: bool = Query(False, description="強制再処理")):
    """データを更新（同期処理）"""
    if not DATA_UPDATER_AVAILABLE:
        raise HTTPException(status_code=503, detail="データ更新機能が利用できません")
    
    try:
        updater = DataUpdater()
        result = updater.update_data(force_reprocess=force)
        
        # 更新後、データを再読み込み
        load_data()
        
        return {
            "message": "データ更新が完了しました",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"データ更新エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"データ更新に失敗しました: {str(e)}")

# 定点把握疾患用エンドポイント
@app.get("/sentinel/summary")
async def get_sentinel_summary(
    start_year: Optional[int] = Query(None, description="開始年"),
    end_year: Optional[int] = Query(None, description="終了年")
):
    """定点把握疾患のサマリー統計を取得"""
    if not sentinel_summary_stats:
        raise HTTPException(status_code=404, detail="定点把握疾患サマリーデータが見つかりません")
    
    if start_year is None and end_year is None:
        return sentinel_summary_stats
    
    # 期間フィルタリングが指定された場合、データを再計算
    if sentinel_data is None or sentinel_data.empty:
        raise HTTPException(status_code=404, detail="定点把握疾患データが見つかりません")
    
    filtered_data = sentinel_data.copy()
    
    if start_year:
        filtered_data = filtered_data[filtered_data['year'] >= start_year]
    if end_year:
        filtered_data = filtered_data[filtered_data['year'] <= end_year]
    
    if filtered_data.empty:
        raise HTTPException(status_code=404, detail="指定された条件のデータが見つかりません")
    
    # フィルタリングされたデータで統計を再計算
    total_records = len(filtered_data)
    years_covered = sorted(filtered_data['year'].unique().tolist())
    total_diseases = filtered_data['disease_name'].nunique()
    
    top_diseases = filtered_data.groupby('disease_name')['total_count'].sum().sort_values(ascending=False).head(10).to_dict()
    yearly_totals = filtered_data.groupby('year')['total_count'].sum().to_dict()
    
    # yearly_totalsのキーを文字列に変換
    yearly_totals = {str(year): int(count) for year, count in yearly_totals.items()}
    
    date_range = {
        "start_year": int(filtered_data['year'].min()),
        "end_year": int(filtered_data['year'].max())
    }
    
    return {
        "total_records": total_records,
        "date_range": date_range,
        "years_covered": years_covered,
        "total_diseases": total_diseases,
        "top_diseases": {disease: int(count) for disease, count in top_diseases.items()},
        "yearly_totals": yearly_totals
    }

@app.get("/sentinel/diseases")
async def get_sentinel_diseases():
    """定点把握疾患リストを取得"""
    if not sentinel_disease_list:
        raise HTTPException(status_code=404, detail="定点把握疾患リストが見つかりません")
    
    return {"diseases": sentinel_disease_list}

@app.get("/sentinel/diseases/{disease_name}/timeseries")
async def get_sentinel_disease_timeseries(
    disease_name: str,
    start_year: Optional[int] = Query(None, description="開始年"),
    end_year: Optional[int] = Query(None, description="終了年")
):
    """特定定点把握疾患の時系列データを取得"""
    if sentinel_data is None or sentinel_data.empty:
        raise HTTPException(status_code=404, detail="定点把握疾患データが見つかりません")
    
    # 疾病名でフィルタリング
    disease_data = sentinel_data[sentinel_data['disease_name'] == disease_name].copy()
    
    if disease_data.empty:
        raise HTTPException(status_code=404, detail=f"定点把握疾患 '{disease_name}' のデータが見つかりません")
    
    # 年範囲でフィルタリング
    if start_year:
        disease_data = disease_data[disease_data['year'] >= start_year]
    if end_year:
        disease_data = disease_data[disease_data['year'] <= end_year]
    
    if disease_data.empty:
        raise HTTPException(status_code=404, detail="指定された条件のデータが見つかりません")
    
    # 年と週でソート
    disease_data = disease_data.sort_values(['year', 'week'])
    
    # 時系列データを作成
    timeseries_data = []
    for _, row in disease_data.iterrows():
        # week_dateから日付を生成（例: 2015-W01 -> 2015-01-05）
        year = row['year']
        week = row['week']
        # 簡易的に週の開始日を計算（実際の週の開始日は複雑なので、年-週形式で返す）
        date_str = f"{year}-W{week:02d}"
        timeseries_data.append({
            "date": date_str,
            "value": int(row['total_count'])
        })
    
    return {
        "disease_name": disease_name,
        "data": timeseries_data,
        "total_records": len(timeseries_data)
    }

@app.get("/sentinel/diseases/top")
async def get_sentinel_top_diseases(
    limit: int = Query(10, description="取得件数"),
    year: Optional[int] = Query(None, description="対象年"),
    start_year: Optional[int] = Query(None, description="開始年"),
    end_year: Optional[int] = Query(None, description="終了年")
):
    """定点把握疾患の報告数上位を取得"""
    if sentinel_data is None or sentinel_data.empty:
        raise HTTPException(status_code=404, detail="定点把握疾患データが見つかりません")
    
    data = sentinel_data.copy()
    
    # 年でフィルタリング
    if year:
        data = data[data['year'] == year]
        if data.empty:
            raise HTTPException(status_code=404, detail=f"{year}年のデータが見つかりません")
    
    # 期間フィルタリング
    if start_year:
        data = data[data['year'] >= start_year]
    if end_year:
        data = data[data['year'] <= end_year]
    
    if data.empty:
        raise HTTPException(status_code=404, detail="指定された条件のデータが見つかりません")
    
    # 疾病別合計を計算
    top_diseases = data.groupby('disease_name')['total_count'].sum().sort_values(ascending=False).head(limit)
    
    result = []
    for disease, count in top_diseases.items():
        result.append({
            "disease_name": disease,
            "total_count": int(count)
        })
    
    return {
        "top_diseases": result,
        "year": year,
        "total_diseases": len(result)
    }

@app.get("/sentinel/yearly-trends")
async def get_sentinel_yearly_trends(
    start_year: Optional[int] = Query(None, description="開始年"),
    end_year: Optional[int] = Query(None, description="終了年")
):
    """定点把握疾患の年別発生動向を取得"""
    if sentinel_data is None or sentinel_data.empty:
        raise HTTPException(status_code=404, detail="定点把握疾患データが見つかりません")
    
    data = sentinel_data.copy()
    
    # 期間フィルタリング
    if start_year:
        data = data[data['year'] >= start_year]
    if end_year:
        data = data[data['year'] <= end_year]
    
    if data.empty:
        raise HTTPException(status_code=404, detail="指定された条件のデータが見つかりません")
    
    yearly_data = data.groupby('year')['total_count'].sum().sort_index()
    
    result = []
    for year, count in yearly_data.items():
        result.append({
            "year": int(year),
            "total_count": int(count)
        })
    
    return {"yearly_trends": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)