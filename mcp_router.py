from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

router = APIRouter(tags=["健康数据接收"])


@router.get("/push")
async def receive_health_data(
    date: str = Query(...),
    active_energy_burned: int = Query(0),
    sleep_start: str = Query(None),
    sleep_end: str = Query(None),
    heart_rate_avg: float = Query(0.0),
    heart_rate_min: float = Query(0.0),
    heart_rate_max: float = Query(0.0),
    is_period: int = Query(0),
    weight: float = Query(0.0),        # ← 新增
    dietary_energy: float = Query(0.0) # ← 新增
):
    try:
        from database import save_memory
        from datetime import datetime, timedelta
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")  # ← 这行之前漏掉了
        health_summary = (
            f"📅 {date}（今日记录）\n"
            f"昨日运动耗能：{active_energy_burned} 步（{yesterday} 全天）\n"
            f"昨日睡眠时间：{sleep_start}（夜间或凌晨入睡）~ {sleep_end}（今早起床）\n"
            f"昨日平均心率：{heart_rate_avg} 次/分（最低{heart_rate_min}，最高{heart_rate_max}）\n"
            f"今日经期状态：{'是' if is_period == 1 else '否'}"
            f"昨日体重：{f'{weight} kg（{yesterday}）' if weight > 0 else '未测量'}\n"                           # ← 新增
            f"昨日膳食能量摄入：{dietary_energy} 千卡\n"    # ← 新增
        )
        await save_memory(content=health_summary, importance=5, source_session="ios_health")
        return {"status": "success"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
