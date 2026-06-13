import asyncio
from src.main import main


def test_run_actor():
    asyncio.run(main())
