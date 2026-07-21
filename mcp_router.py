from fastapi import APIRouter, Query
from database import save_memory
from datetime import datetime

# 创建一个专门接收健康数据的路由组
router = APIRouter(prefix="/api/health", tags=["健康数据"])

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
        # 1. 把零散数据拼成 AI 容易读懂的一段自然语言（这就是“记忆”）
        health_summary = (
            f"📅 {date}\n"
            f"走路步数：{steps} 步\n"
            f"睡眠时间：{sleep_start} ~ {sleep_end}\n"
            f"平均心率：{heart_rate_avg} 次/分 (最低{heart_rate_min}，最高{heart_rate_max})\n"
            f"经期状态：{'是' if is_period == 1 else '否'}"
        )

        # 2. 调用项目底层自带的 save_memory，直接存入你的 Supabase
        # 参数：content（内容），importance（重要性默认5），source_session（来源标记）
        await save_memory(content=health_summary, importance=5, source_session="ios_health")

        print(f"✅ 健康数据已成功存入记忆库: {health_summary}")
        return {"status": "success", "message": "健康数据已记录到记忆库"}

    except Exception as e:
        print(f"❌ 接收健康数据出错: {e}")
        return {"status": "error", "message": str(e)}
