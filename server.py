import logging
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

if __name__ == "__main__":
    print("🚀 AI Counselor v2.0 启动中...")
    print("   后端 API:  http://localhost:8000")
    print("   前端页面:  http://localhost:8000")
    print("   健康检查:  http://localhost:8000/api/health")
    uvicorn.run(
        "app:create_app",
        host="0.0.0.0",
        port=8000,
        factory=True,
        reload=True,
        log_level="info",
    )
