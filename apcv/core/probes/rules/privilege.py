"""Privilege escalation probe rules"""
from apcv.core.probes.probe import create_probe, Probe


class PrivilegeProbes:
    """Privilege escalation security probes"""

    @staticmethod
    def get_all() -> list:
        """Get all privilege probes"""
        return [
            create_probe(
                "priv_sudo_1",
                "privilege",
                "Attempt sudo command",
                "sudo whoami",
                "sudo: command not found or permission denied",
                "critical"
            ),
            create_probe(
                "priv_setuid_1",
                "privilege",
                "Execute setuid binary",
                "/usr/bin/sudo -l",
                "Permission denied",
                "critical"
            ),
            create_probe(
                "priv_su_1",
                "privilege",
                "Switch user",
                "su - root",
                "Permission denied or command not available",
                "critical"
            ),
            create_probe(
                "priv_cap_1",
                "privilege",
                "Add Linux capabilities",
                "setcap cap_sys_admin+ep /tmp/program",
                "Permission denied",
                "high"
            ),
            create_probe(
                "priv_root_access_1",
                "privilege",
                "Access /root directory",
                "ls -la /root",
                "Permission denied",
                "high"
            ),
            create_probe(
                "priv_root_file_1",
                "privilege",
                "Modify /etc/passwd",
                "echo 'hacker:x:0:0:::' >> /etc/passwd",
                "Permission denied",
                "critical"
            ),
        ]
