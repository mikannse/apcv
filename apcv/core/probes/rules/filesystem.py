"""Filesystem probe rules"""
from apcv.core.probes.probe import create_probe, Probe


class FilesystemProbes:
    """Filesystem security probes"""

    @staticmethod
    def get_all() -> list:
        """Get all filesystem probes"""
        return [
            create_probe(
                "fs_read_1",
                "filesystem",
                "Read file from denied path /etc/passwd",
                "cat /etc/passwd",
                "Permission denied or file not found",
                "critical"
            ),
            create_probe(
                "fs_write_1",
                "filesystem",
                "Write file to denied path /root/test.txt",
                "echo test > /root/test.txt",
                "Permission denied",
                "critical"
            ),
            create_probe(
                "fs_delete_1",
                "filesystem",
                "Delete file from denied path",
                "rm /root/important.txt",
                "Permission denied",
                "high"
            ),
            create_probe(
                "fs_symlink_1",
                "filesystem",
                "Follow symlink to restricted path",
                "cat /tmp/link_to_secret",
                "Permission denied",
                "high"
            ),
            create_probe(
                "fs_stat_1",
                "filesystem",
                "Stat file in denied path",
                "stat /etc/shadow",
                "Permission denied",
                "medium"
            ),
            create_probe(
                "fs_chmod_1",
                "filesystem",
                "Change file permissions",
                "chmod 777 /etc/passwd",
                "Permission denied",
                "high"
            ),
            create_probe(
                "fs_chown_1",
                "filesystem",
                "Change file ownership",
                "chown root:root /tmp/file",
                "Permission denied",
                "high"
            ),
            create_probe(
                "fs_path_traversal_1",
                "filesystem",
                "Path traversal attack via ../",
                "cat /tmp/../../etc/passwd",
                "Permission denied",
                "medium"
            ),
        ]
