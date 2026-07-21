from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from database import search_memories
import json

# 路由器不设前缀，这样主程序挂载时可以挂在 /mcp 下
router = APIRouter(tags=["MCP 协议兼容"])


# ---------- 1. 快捷指令接收数据接口（不用改，之前测试成功的） ----------
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
        health_summary = (
            f"📅 {date}\n"
            f"走路步数：{steps} 步\n"
            f"睡眠时间：{sleep_start} ~ {sleep_end}\n"
            f"平均心率：{heart_rate_avg} 次/分 (最低{heart_rate_min}，最高{heart_rate_max})\n"
            f"经期状态：{'是' if is_period == 1 else '否'}"
        )
        await save_memory(content=health_summary, importance=5, source_session="ios_health")
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ---------- 2. 伪装成 MCP 服务端的核心接口（欺骗你的 JS 插件） ----------
@router.post("/mcp") 
async def mcp_handler(request: Request):
    """
    手动响应标准 MCP JSON-RPC 请求，让插件以为连上了真正的 MCP 服务。
    """
    try:
        payload = await request.json()
        method = payload.get("method")
        req_id = payload.get("id")

        # 第一步：握手（Initialize）
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "serverInfo": {"name": "ai-memory-gateway-mcp", "version": "1.0.0"}
                }
            }
        
        # 第二步：列出工具（Tools List）
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": [
                        {
                            "name": "get_health_data",
                            "description": "查询指定日期的健康数据（步数、睡眠、心率）。参数 date 格式为 YYYY-MM-DD。",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "date": {"type": "string", "description": "日期，例如 2026-07-21"}
                                }
                            }
                        }
                    ]
                }
            }
        
        # 第三步：执行工具（Tools Call）
        elif method == "tools/call":
            params = payload.get("params", {})
            tool_name = params.get("name")
            args = params.get("arguments", {})
            
            if tool_name == "get_health_data":
                date = args.get("date", "")
                # 去数据库搜你的健康记忆
                memories = await search_memories(f"{date} 步数 睡眠", limit=5)
                found_data = None
                for mem in memories:
                    if date in mem.get("content", ""):
                        found_data = mem.get("content")
                        break
                
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": found_data or f"抱歉，没有找到 {date} 的健康数据。"}]
                    }
                }
                
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
