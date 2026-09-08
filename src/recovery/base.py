"""Shared types for recovery tools."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FixResult:
    success: bool
    message: str
    output: str = ""