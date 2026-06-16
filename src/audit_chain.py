import hashlib


class AuditChain:
    _REDIS_KEY = "audit_chain:previous_hash"
    _INITIAL_HASH = "0" * 64

    @classmethod
    async def anchor(cls, entry_id: str, timestamp: str, agent: str, action: str, details: str) -> str:
        from src.cache import get_redis
        redis = await get_redis()
        prev = await redis.get(cls._REDIS_KEY) or cls._INITIAL_HASH
        payload = f"{entry_id}{timestamp}{agent}{action}{details}{prev}"
        block_hash = hashlib.sha256(payload.encode()).hexdigest()
        await redis.set(cls._REDIS_KEY, block_hash)
        return block_hash

    @classmethod
    def verify_chain(cls, entries: list[dict]) -> bool:
        prev = cls._INITIAL_HASH
        for e in entries:
            payload = f"{e['id']}{e['timestamp']}{e['agent']}{e['action_type']}{e['details']}{prev}"
            expected = hashlib.sha256(payload.encode()).hexdigest()
            if e.get("chain_hash") != expected:
                return False
            prev = expected
        return True
