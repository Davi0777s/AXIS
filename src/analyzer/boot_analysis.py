"""Boot image analyzer — unpacks, inspects, and reports on Android boot images."""
from __future__ import annotations
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_MAX_BOOT_BYTES = 2 * 1024 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class BootHeader:
    magic: str
    kernel_size: int
    kernel_addr: int
    ramdisk_size: int
    ramdisk_addr: int
    second_size: int
    second_addr: int
    tags_addr: int
    page_size: int
    header_version: int
    os_version: int
    name: str
    cmdline: str


@dataclass(frozen=True, slots=True)
class AnalysisReport:
    file_path: str
    file_size: int
    header: BootHeader | None
    is_valid: bool
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        if not self.is_valid:
            return f"Invalid: {'; '.join(self.issues)}"
        if not self.header:
            return "Valid (no header details)"
        parts = [
            f"Boot v{self.header.header_version}",
            f"Kernel: {self._fmt(self.header.kernel_size)}",
            f"Ramdisk: {self._fmt(self.header.ramdisk_size)}",
            f"Page: {self.header.page_size}B",
        ]
        return " | ".join(parts)

    @staticmethod
    def _fmt(size: int) -> str:
        if size < 1024:
            return f"{size} B"
        if size < 1048576:
            return f"{size / 1024:.1f} KB"
        return f"{size / 1048576:.1f} MB"

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "file": self.file_path,
            "size": self.file_size,
            "valid": self.is_valid,
            "issues": self.issues,
            "recommendations": self.recommendations,
        }
        if self.header:
            d["header"] = {
                "magic": self.header.magic,
                "kernel_size": self.header.kernel_size,
                "ramdisk_size": self.header.ramdisk_size,
                "page_size": self.header.page_size,
                "version": self.header.header_version,
                "name": self.header.name,
                "cmdline": self.header.cmdline,
            }
        return d


class BootAnalyzer:
    MAGIC = b"ANDROID!"
    VENDOR_MAGIC = b"VNDRBOOT"

    def analyze(self, file_path: str | Path) -> AnalysisReport:
        path = Path(file_path)
        issues: list[str] = []
        recs: list[str] = []

        if not path.exists():
            return AnalysisReport(str(path), 0, None, False, ["File does not exist"])

        try:
            size = path.stat().st_size
        except OSError:
            return AnalysisReport(str(path), 0, None, False, ["Cannot read file"])
        if size > _MAX_BOOT_BYTES:
            return AnalysisReport(
                str(path), size, None, False,
                [f"File too large ({size} B, max {_MAX_BOOT_BYTES} B)"],
            )

        data = path.read_bytes()

        if size < 1632:
            return AnalysisReport(str(path), size, None, False, [f"Too small ({size} B)"])

        if data[:8] == self.VENDOR_MAGIC:
            return self._vendor_boot(path, data, issues, recs)

        if data[:8] != self.MAGIC:
            return AnalysisReport(str(path), size, None, False, ["Bad magic bytes"])

        header = self._parse_boot(data, issues, recs)
        if not header:
            return AnalysisReport(str(path), size, None, False, issues)

        if header.page_size not in (2048, 4096, 16384):
            issues.append(f"Unusual page size: {header.page_size}")
        if header.header_version > 4:
            issues.append(f"Unknown header version: {header.header_version}")

        return AnalysisReport(str(path), size, header, True, issues, recs)

    def _parse_boot(self, data: bytes, issues: list[str], recs: list[str]) -> BootHeader | None:
        try:
            return BootHeader(
                magic=data[:8].decode("ascii"),
                kernel_size=struct.unpack_from("<I", data, 8)[0],
                kernel_addr=struct.unpack_from("<I", data, 12)[0],
                ramdisk_size=struct.unpack_from("<I", data, 16)[0],
                ramdisk_addr=struct.unpack_from("<I", data, 20)[0],
                second_size=struct.unpack_from("<I", data, 24)[0],
                second_addr=struct.unpack_from("<I", data, 28)[0],
                tags_addr=struct.unpack_from("<I", data, 32)[0],
                page_size=struct.unpack_from("<I", data, 36)[0],
                header_version=struct.unpack_from("<I", data, 40)[0],
                os_version=struct.unpack_from("<I", data, 44)[0],
                name=data[64:80].split(b"\x00", 1)[0].decode("ascii", errors="replace"),
                cmdline=data[512:1024].split(b"\x00", 1)[0].decode("ascii", errors="replace"),
            )
        except (struct.error, UnicodeDecodeError) as exc:
            issues.append(f"Parse error: {exc}")
            return None

    def _vendor_boot(self, path: Path, data: bytes, issues: list[str], recs: list[str]) -> AnalysisReport:
        try:
            hv = struct.unpack_from("<I", data, 8)[0]
            ps = struct.unpack_from("<I", data, 12)[0]
            ka = struct.unpack_from("<I", data, 16)[0]
            rs = struct.unpack_from("<I", data, 28)[0]
            header = BootHeader("VNDRBOOT", 0, ka, rs, 0, 0, 0, 0, ps, hv, 0, "vendor_boot", "")
            if hv > 4:
                issues.append(f"Unknown vendor boot version: {hv}")
            return AnalysisReport(str(path), len(data), header, True, issues, recs)
        except struct.error as exc:
            return AnalysisReport(str(path), len(data), None, False, [f"Vendor boot parse error: {exc}"])
