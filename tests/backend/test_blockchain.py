import os
import pytest

os.environ["SECRET_KEY"] = "test-secret-key-for-ci"

from backend.services.blockchain import _guess_bitcoin_type


def test_bitcoin_type_guessing():
    assert "P2PKH" in _guess_bitcoin_type("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    assert "P2SH" in _guess_bitcoin_type("3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy")
    assert "Bech32" in _guess_bitcoin_type("bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq")
    assert _guess_bitcoin_type("unknown123") == "unknown"


@pytest.mark.asyncio
async def test_analyze_bitcoin_invalid():
    from backend.services.blockchain import analyze_address
    result = await analyze_address("bitcoin", "invalid_address")
    assert result["valid_format"] is False


@pytest.mark.asyncio
async def test_analyze_ethereum_invalid():
    from backend.services.blockchain import analyze_address
    result = await analyze_address("ethereum", "0xshort")
    assert result["valid_format"] is False


@pytest.mark.asyncio
async def test_analyze_monero_invalid():
    from backend.services.blockchain import analyze_address
    result = await analyze_address("monero", "short")
    assert result["valid_format"] is False


@pytest.mark.asyncio
async def test_unsupported_chain():
    from backend.services.blockchain import analyze_address
    result = await analyze_address("solana", "someaddress")
    assert "error" in result
