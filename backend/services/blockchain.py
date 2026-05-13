from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from backend.models.blockchain import BlockchainAnalysis, WalletRecovery
from backend.core.config import get_settings
from backend.core.http_client import create_client

settings = get_settings()


async def analyze_address(chain: str, address: str) -> dict:
    chain_lower = chain.lower()
    if chain_lower == "bitcoin":
        return await _analyze_bitcoin(address)
    elif chain_lower in ("ethereum", "eth"):
        return await _analyze_ethereum(address)
    elif chain_lower == "monero":
        return await _analyze_monero(address)
    else:
        return {"error": f"Unsupported chain: {chain}"}


async def _analyze_bitcoin(address: str) -> dict:
    result = {
        "chain": "bitcoin",
        "address": address,
        "valid_format": False,
        "type": _guess_bitcoin_type(address),
        "balance": None,
        "total_received": None,
        "total_sent": None,
        "transaction_count": None,
        "first_tx": None,
        "last_tx": None,
        "risk_indicators": [],
    }
    valid_prefixes = ("1", "3", "bc1")
    if not address.startswith(valid_prefixes):
        result["valid_format"] = False
        return result
    result["valid_format"] = True
    try:
        async with create_client(timeout=10) as client:
            resp = await client.get(f"https://blockchain.info/rawaddr/{address}")
            if resp.status_code == 200:
                data = resp.json()
                result["balance"] = data.get("final_balance", 0) / 1e8
                result["total_received"] = data.get("total_received", 0) / 1e8
                result["total_sent"] = data.get("total_sent", 0) / 1e8
                result["transaction_count"] = data.get("n_tx", 0)
                if data.get("first_tx"):
                    result["first_tx"] = datetime.utcfromtimestamp(data["first_tx"]).isoformat()
                if data.get("last_tx"):
                    result["last_tx"] = datetime.utcfromtimestamp(data["last_tx"]).isoformat()
            else:
                result["note"] = f"Blockchain.info API error: {resp.status_code}"
    except httpx.RequestError as e:
        result["note"] = f"Blockchain.info unreachable: {e}"
    return result


async def _analyze_ethereum(address: str) -> dict:
    result = {
        "chain": "ethereum",
        "address": address,
        "valid_format": False,
        "type": "invalid",
        "balance_eth": None,
        "transaction_count": None,
        "is_contract": None,
        "risk_indicators": [],
    }
    is_valid = address.startswith("0x") and len(address) == 42
    if not is_valid:
        return result
    result["valid_format"] = True
    result["type"] = "EOA"
    api_key = settings.ETHERSCAN_API_KEY
    if not api_key:
        result["note"] = "Set ETHERSCAN_API_KEY for on-chain data"
        return result
    try:
        async with create_client(timeout=10) as client:
            resp = await client.get(
                "https://api.etherscan.io/api",
                params={
                    "module": "account",
                    "action": "balance",
                    "address": address,
                    "tag": "latest",
                    "apikey": api_key,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "1":
                    result["balance_eth"] = int(data["result"]) / 1e18
            resp2 = await client.get(
                "https://api.etherscan.io/api",
                params={
                    "module": "account",
                    "action": "txlist",
                    "address": address,
                    "startblock": 0,
                    "endblock": 99999999,
                    "page": 1,
                    "offset": 1,
                    "sort": "desc",
                    "apikey": api_key,
                },
            )
            if resp2.status_code == 200:
                data2 = resp2.json()
                if data2.get("status") == "1":
                    result["transaction_count"] = len(data2.get("result", []))
    except httpx.RequestError as e:
        result["note"] = f"Etherscan unreachable: {e}"
    return result


async def _analyze_monero(address: str) -> dict:
    result = {
        "chain": "monero",
        "address": address,
        "valid_format": False,
        "type": "invalid",
        "balance": None,
        "transaction_count": None,
        "risk_indicators": [],
    }
    is_valid = address.startswith("4") and len(address) in (95, 106)
    if not is_valid:
        result["valid_format"] = False
        return result
    result["valid_format"] = True
    result["type"] = "standard" if len(address) == 95 else "subaddress"
    try:
        async with create_client(timeout=10) as client:
            resp = await client.post(
                "https://xmrchain.net/api/check_outputs",
                json={"address": address, "raw": False, "viewkey": ""},
            )
            if resp.status_code == 200:
                data = resp.json()
                result["transaction_count"] = len(data.get("outputs", []))
            resp2 = await client.get(
                f"https://xmrchain.net/api/balance/{address}",
            )
            if resp2.status_code == 200:
                data2 = resp2.json()
                result["balance"] = data2.get("balance", 0) / 1e12
    except httpx.RequestError:
        result["note"] = "xmrchain.net unreachable"
    return result


def _guess_bitcoin_type(address: str) -> str:
    if address.startswith("1"):
        return "P2PKH (Legacy)"
    elif address.startswith("3"):
        return "P2SH (SegWit-compatible)"
    elif address.startswith("bc1"):
        return "Bech32 (Native SegWit)"
    return "unknown"


def store_analysis(db: Session, user_id: Optional[int], chain: str, address: str, analysis: dict) -> BlockchainAnalysis:
    record = BlockchainAnalysis(
        user_id=user_id,
        chain=chain,
        address=address,
        analysis_type="address_lookup",
        risk_score=analysis.get("risk_score"),
        report=analysis,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_recent_analyses(db: Session, user_id: Optional[int] = None, limit: int = 20) -> list[BlockchainAnalysis]:
    query = db.query(BlockchainAnalysis)
    if user_id:
        query = query.filter(BlockchainAnalysis.user_id == user_id)
    return query.order_by(BlockchainAnalysis.created_at.desc()).limit(limit).all()


def create_recovery(db: Session, user_id: Optional[int], chain: str, method: str) -> WalletRecovery:
    recovery = WalletRecovery(user_id=user_id, chain=chain, method=method)
    db.add(recovery)
    db.commit()
    db.refresh(recovery)
    return recovery


def get_recoveries(db: Session, user_id: Optional[int] = None) -> list[WalletRecovery]:
    query = db.query(WalletRecovery)
    if user_id:
        query = query.filter(WalletRecovery.user_id == user_id)
    return query.order_by(WalletRecovery.created_at.desc()).all()
