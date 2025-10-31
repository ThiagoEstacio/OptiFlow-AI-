"""
Gateway entry point when run as module
"""
import asyncio
from app.main import main

if __name__ == "__main__":
    asyncio.run(main())
