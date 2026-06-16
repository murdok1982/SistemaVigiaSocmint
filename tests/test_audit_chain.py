import pytest
from unittest.mock import AsyncMock, patch
from src.audit_chain import AuditChain


@pytest.mark.asyncio
async def test_anchor_generates_hash():
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock()
    with patch("src.cache.get_redis", return_value=mock_redis):
        hash1 = await AuditChain.anchor("id1", "2024-01-01T00:00:00", "AUTH", "login", "test")
    assert len(hash1) == 64
    assert all(c in "0123456789abcdef" for c in hash1)


@pytest.mark.asyncio
async def test_anchor_chain_linking():
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock()
    with patch("src.cache.get_redis", return_value=mock_redis):
        hash1 = await AuditChain.anchor("id1", "t1", "A1", "act1", "d1")
        mock_redis.get = AsyncMock(return_value=hash1)
        hash2 = await AuditChain.anchor("id2", "t2", "A2", "act2", "d2")
    assert hash1 != hash2


@pytest.mark.asyncio
async def test_verify_valid_chain():
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock()
    entries = []
    with patch("src.cache.get_redis", return_value=mock_redis):
        for i in range(3):
            entry_id = f"id{i}"
            ts = f"t{i}"
            agent = f"A{i}"
            action = f"act{i}"
            details = f"d{i}"
            chain_hash = await AuditChain.anchor(entry_id, ts, agent, action, details)
            mock_redis.get = AsyncMock(return_value=chain_hash)
            entries.append({
                "id": entry_id, "timestamp": ts, "agent": agent,
                "action_type": action, "details": details, "chain_hash": chain_hash
            })
    assert AuditChain.verify_chain(entries) is True


@pytest.mark.asyncio
async def test_verify_tampered_chain():
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock()
    entries = []
    with patch("src.cache.get_redis", return_value=mock_redis):
        for i in range(3):
            entry_id = f"id{i}"
            ts = f"t{i}"
            agent = f"A{i}"
            action = f"act{i}"
            details = f"d{i}"
            chain_hash = await AuditChain.anchor(entry_id, ts, agent, action, details)
            mock_redis.get = AsyncMock(return_value=chain_hash)
            entries.append({
                "id": entry_id, "timestamp": ts, "agent": agent,
                "action_type": action, "details": details, "chain_hash": chain_hash
            })
    entries[1]["details"] = "TAMPERED"
    assert AuditChain.verify_chain(entries) is False
