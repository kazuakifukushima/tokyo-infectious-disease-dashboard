#!/usr/bin/env python3
"""
定期的なデータ更新を実行するスクリプト
cronやGitHub Actionsから呼び出し可能
"""

import os
import sys
import logging
import json
from datetime import datetime

# バックエンドディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_updater import DataUpdater

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_update.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """メイン実行関数"""
    logger.info("=" * 60)
    logger.info("データ更新処理を開始します")
    logger.info(f"実行日時: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    try:
        updater = DataUpdater()
        
        # 更新状態を確認
        status = updater.get_update_status()
        logger.info(f"更新前の状態: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
        # データを更新
        result = updater.update_data(force_reprocess=False)
        
        logger.info("=" * 60)
        logger.info("データ更新処理が完了しました")
        logger.info(f"結果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        logger.info("=" * 60)
        
        # 結果に基づいて終了コードを設定
        if result.get("success"):
            sys.exit(0)
        else:
            logger.error("データ更新に失敗しました")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

