"""Network probe rules"""
from apcv.core.probes.probe import create_probe, Probe


class NetworkProbes:
    """Network security probes"""

    @staticmethod
    def get_all() -> list:
        """Get all network probes"""
        return [
            create_probe(
                "net_outbound_1",
                "network",
                "Outbound network connection",
                "curl http://external.com",
                "Connection refused or network access denied",
                "shell",
                "critical"
            ),
            create_probe(
                "net_dns_1",
                "network",
                "DNS query",
                "nslookup google.com",
                "Query failed or network access denied",
                "shell",
                "high"
            ),
            create_probe(
                "net_denied_domain_1",
                "network",
                "Connect to denied domain",
                "curl http://malicious.com",
                "Connection refused",
                "shell",
                "high"
            ),
            create_probe(
                "net_port_1",
                "network",
                "Connect to unauthorized port",
                "nc -zv 192.168.1.1 22",
                "Connection refused",
                "shell",
                "medium"
            ),
            create_probe(
                "net_raw_socket_1",
                "network",
                "Create raw socket",
                "python3 -c 'import socket; s = socket.socket(socket.AF_INET, socket.SOCK_RAW)'",
                "Permission denied",
                "shell",
                "high"
            ),
            create_probe(
                "net_listen_1",
                "network",
                "Listen on network port",
                "python3 -c 'import socket; s = socket.socket(); s.bind((\"0.0.0.0\", 8888))'",
                "Permission denied",
                "shell",
                "high"
            ),
        ]
