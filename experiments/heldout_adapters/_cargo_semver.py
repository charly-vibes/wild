# Purpose: Cargo requirement semantics shared by the held-out adapters.
# Responsibilities: Parse three-component versions and evaluate Cargo's
#   documented caret (^), tilde (~), exact (=), and plain (implicit caret)
#   requirement forms against a candidate version.
# Rationale: host-ranges and ecosystem adapters must apply the ecosystem's
#   real compatibility rules, not ad-hoc ones. Unparseable requirements raise
#   so callers can emit an honest error verdict instead of guessing.

from __future__ import annotations


def parse_version(text: str) -> tuple[int, int, int]:
    parts = text.strip().split(".")
    if not 1 <= len(parts) <= 3 or not all(p.isdigit() for p in parts):
        raise ValueError(f"unsupported version: {text!r}")
    numbers = [int(p) for p in parts]
    while len(numbers) < 3:
        numbers.append(0)
    return (numbers[0], numbers[1], numbers[2])


def _caret(base: tuple[int, int, int], target: tuple[int, int, int]) -> bool:
    if base[0] > 0:
        return target >= base and target[0] == base[0]
    if base[1] > 0:
        return target >= base and target[0] == 0 and target[1] == base[1]
    return target == base  # 0.0.z: only that exact patch


def _tilde(base: tuple[int, int, int], components: int,
           target: tuple[int, int, int]) -> bool:
    if components >= 2:
        return target >= base and target[0] == base[0] and target[1] == base[1]
    return target >= base and target[0] == base[0]


def requirement_allows(requirement: str, version: str) -> bool:
    """Evaluate one Cargo requirement string against a version."""
    req = requirement.strip()
    if req.startswith("="):
        return parse_version(req[1:]) == parse_version(version)
    if req.startswith("^"):
        return _caret(parse_version(req[1:]), parse_version(version))
    if req.startswith("~"):
        rest = req[1:].strip()
        return _tilde(parse_version(rest), len(rest.split(".")),
                      parse_version(version))
    if req and req[0].isdigit():
        return _caret(parse_version(req), parse_version(version))
    raise ValueError(f"unsupported requirement form: {requirement!r}")


def cargo_caret_compatible(base: str, target: str) -> bool:
    """Cargo's caret compatibility ruling between two concrete versions."""
    return _caret(parse_version(base), parse_version(target))