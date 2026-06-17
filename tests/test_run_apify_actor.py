import pytest
from src.main import main


@pytest.mark.asyncio
async def test_run_actor():
    await main()
