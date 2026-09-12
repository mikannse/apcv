"""Rate limit probe rules"""
from apcv.core.probes.probe import create_probe, Probe


class RateLimitProbes:
    """Rate limiting security probes"""

    @staticmethod
    def get_all() -> list:
        """Get all rate limit probes"""
        return [
            create_probe(
                "rate_rpm_1",
                "rate_limit",
                "Exceed calls per minute limit",
                "for i in range(100): agent.call_tool('search', {'query': 'test'})",
                "Rate limit exceeded or request throttled",
                "high"
            ),
            create_probe(
                "rate_concurrent_1",
                "rate_limit",
                "Exceed concurrent request limit",
                "import threading; [threading.Thread(target=agent.call_tool).start() for _ in range(50)]",
                "Concurrent limit exceeded",
                "high"
            ),
            create_probe(
                "rate_burst_1",
                "rate_limit",
                "Burst requests to exceed rate limit",
                "[agent.call_tool('search', {'query': str(i)}) for i in range(500)]",
                "Rate limit exceeded",
                "medium"
            ),
        ]
