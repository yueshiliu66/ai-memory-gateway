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

# ---------- 追加 MCP 工具（需要从 main.py 导入 mcp 对象） ----------
from main import mcp
from database import search_memories

@mcp.tool()
async def get_health_data(date: str) -> str:
    """
    查询指定日期的健康数据（步数、睡眠、心率等）。
    参数 date 格式为 YYYY-MM-DD，例如：2026-07-21。
    """
    try:
        # 自动去数据库搜包含这个日期的健康记录
        memories = await search_memories(f"{date} 步数 睡眠 心率", limit=5)
        
        if not memories:
            return f"没有找到 {date} 的健康数据记录。"
        
        # 提取最符合的那条（因为之前存进去的是一段自然语言描述）
        for mem in memories:
            content = mem.get("content", "")
            # 如果搜到的这段内容包含日期，说明就是我们存进去的健康数据
            if date in content:
                return f"这是我为你查到的 {date} 健康数据：\n{content}"
        
        return f"找到了相关记忆，但没有精确匹配 {date} 的完整健康数据。"
        
    except Exception as e:
        return f"查询数据库时出错：{str(e)}"
