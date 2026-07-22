from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

router = APIRouter(tags=["健康数据接收"])


@router.get("/push")
async def receive_health_data(
    date: str = Query(...),
    steps: int = Query(0),
    sleep_start: str = Query(None),
    sleep_end: str = Query(None),
    heart_rate_avg: float = Query(0.0),
    heart_rate_min: float = Query(0.0),
    heart_rate_max: float = Query(0.0),
    is_period: int = Query(0)
):
    try:
        from database import save_memory
        from datetime import datetime, timedelta
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")  # ← 这行之前漏掉了
        health_summary = (
            f"📅 {date}（今日记录）\n"
            f"走路步数：{steps} 步（{yesterday} 全天）\n"
            f"睡眠时间：{sleep_start}（昨晚入睡）~ {sleep_end}（今早起床）\n"
            f"平均心率：{heart_rate_avg} 次/分（最低{heart_rate_min}，最高{heart_rate_max}，{yesterday} 全天）\n"
            f"经期状态：{'是' if is_period == 1 else '否'}（今日）"
        )
        await save_memory(content=health_summary, importance=5, source_session="ios_health")
        return {"status": "success"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
