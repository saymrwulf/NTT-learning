"""Small, inspectable helpers for the first NTT learning module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


def _apply_mod(values: Sequence[int], modulus: int | None) -> list[int]:
    if modulus is None:
        return [int(value) for value in values]
    return [int(value) % modulus for value in values]


def schoolbook_convolution(
    left: Sequence[int], right: Sequence[int], modulus: int | None = None
) -> list[int]:
    """Multiply two coefficient arrays directly."""
    if not left or not right:
        return []

    result = [0] * (len(left) + len(right) - 1)
    for left_index, left_value in enumerate(left):
        for right_index, right_value in enumerate(right):
            result[left_index + right_index] += left_value * right_value
    return _apply_mod(result, modulus)


def negacyclic_reduce(
    coefficients: Sequence[int], n: int, modulus: int | None = None
) -> list[int]:
    """Fold a polynomial back into the ring Z_q[x] / (x^n + 1)."""
    if n <= 0:
        raise ValueError("n must be positive")

    reduced = [0] * n
    for index, coefficient in enumerate(coefficients):
        wraps, slot = divmod(index, n)
        reduced[slot] += coefficient if wraps % 2 == 0 else -coefficient
    return _apply_mod(reduced, modulus)


def negacyclic_multiply(
    left: Sequence[int], right: Sequence[int], n: int, modulus: int | None = None
) -> list[int]:
    """Multiply then fold back into degree < n with sign flips on wraparound."""
    if len(left) != n or len(right) != n:
        raise ValueError("left and right must both have length n")

    return negacyclic_reduce(schoolbook_convolution(left, right), n=n, modulus=modulus)


def mod_inverse(value: int, modulus: int) -> int:
    """Return the multiplicative inverse modulo ``modulus``."""
    return pow(value, -1, modulus)


def _proper_divisors(order: int) -> list[int]:
    return [candidate for candidate in range(1, order) if order % candidate == 0]


def find_primitive_root(order: int, modulus: int) -> int:
    """Find a primitive ``order``-th root of unity in Z_modulus."""
    if order <= 0:
        raise ValueError("order must be positive")
    if (modulus - 1) % order != 0:
        raise ValueError("order must divide modulus - 1")

    for candidate in range(2, modulus):
        if pow(candidate, order, modulus) != 1:
            continue
        if any(pow(candidate, divisor, modulus) == 1 for divisor in _proper_divisors(order)):
            continue
        return candidate

    raise ValueError(f"no primitive {order}-th root exists modulo {modulus}")


def forward_ntt(values: Sequence[int], modulus: int, omega: int) -> list[int]:
    """Definition-first NTT using the matrix viewpoint."""
    n = len(values)
    if n == 0:
        return []

    spectrum = []
    for row in range(n):
        total = 0
        for column, value in enumerate(values):
            total += value * pow(omega, row * column, modulus)
        spectrum.append(total % modulus)
    return spectrum


def inverse_ntt(values: Sequence[int], modulus: int, omega: int) -> list[int]:
    """Inverse transform paired with ``forward_ntt``."""
    n = len(values)
    if n == 0:
        return []

    omega_inverse = mod_inverse(omega, modulus)
    n_inverse = mod_inverse(n, modulus)
    recovered = []
    for row in range(n):
        total = 0
        for column, value in enumerate(values):
            total += value * pow(omega_inverse, row * column, modulus)
        recovered.append((total * n_inverse) % modulus)
    return recovered


def ct_butterfly_pair(top: int, bottom: int, zeta: int, modulus: int) -> tuple[int, int]:
    """One Cooley-Tukey style butterfly on a pair."""
    twiddled = (zeta * bottom) % modulus
    return (top + twiddled) % modulus, (top - twiddled) % modulus


def gs_butterfly_pair(top: int, bottom: int, zeta: int, modulus: int) -> tuple[int, int]:
    """One Gentleman-Sande style butterfly on a pair."""
    summed = (top + bottom) % modulus
    diff = (top - bottom) % modulus
    return summed, (zeta * diff) % modulus


def stage_pairings(length: int, block_size: int) -> list[tuple[int, int]]:
    """Return the index pairings touched by a single butterfly stage."""
    if length <= 0:
        raise ValueError("length must be positive")
    if block_size <= 0 or block_size % 2 != 0:
        raise ValueError("block_size must be a positive even integer")
    if length % block_size != 0:
        raise ValueError("block_size must divide length")

    half = block_size // 2
    pairs: list[tuple[int, int]] = []
    for start in range(0, length, block_size):
        for offset in range(half):
            pairs.append((start + offset, start + offset + half))
    return pairs


def _expand_zetas(zetas: int | Iterable[int], pair_count: int) -> list[int]:
    if isinstance(zetas, int):
        return [zetas] * pair_count

    expanded = [int(zeta) for zeta in zetas]
    if len(expanded) != pair_count:
        raise ValueError(f"expected {pair_count} zetas, received {len(expanded)}")
    return expanded


@dataclass(frozen=True)
class ButterflyAction:
    pair: tuple[int, int]
    zeta: int
    inputs: tuple[int, int]
    outputs: tuple[int, int]


def apply_ct_stage(
    values: Sequence[int], block_size: int, zetas: int | Iterable[int], modulus: int
) -> tuple[list[int], list[ButterflyAction]]:
    """Apply a toy Cooley-Tukey stage and return per-pair trace data."""
    source = list(values)
    updated = list(values)
    pairs = stage_pairings(len(source), block_size)
    zeta_values = _expand_zetas(zetas, len(pairs))
    actions: list[ButterflyAction] = []

    for (left, right), zeta in zip(pairs, zeta_values):
        outputs = ct_butterfly_pair(source[left], source[right], zeta, modulus)
        updated[left], updated[right] = outputs
        actions.append(
            ButterflyAction(
                pair=(left, right),
                zeta=zeta % modulus,
                inputs=(source[left], source[right]),
                outputs=outputs,
            )
        )
    return updated, actions


def apply_gs_stage(
    values: Sequence[int], block_size: int, zetas: int | Iterable[int], modulus: int
) -> tuple[list[int], list[ButterflyAction]]:
    """Apply a toy Gentleman-Sande stage and return per-pair trace data."""
    source = list(values)
    updated = list(values)
    pairs = stage_pairings(len(source), block_size)
    zeta_values = _expand_zetas(zetas, len(pairs))
    actions: list[ButterflyAction] = []

    for (left, right), zeta in zip(pairs, zeta_values):
        outputs = gs_butterfly_pair(source[left], source[right], zeta, modulus)
        updated[left], updated[right] = outputs
        actions.append(
            ButterflyAction(
                pair=(left, right),
                zeta=zeta % modulus,
                inputs=(source[left], source[right]),
                outputs=outputs,
            )
        )
    return updated, actions


def action_rows(actions: Sequence[ButterflyAction]) -> list[dict[str, object]]:
    """Return action traces in a notebook-friendly shape."""
    return [
        {
            "pair": action.pair,
            "zeta": action.zeta,
            "inputs": action.inputs,
            "outputs": action.outputs,
        }
        for action in actions
    ]


def bit_reverse(index: int, width: int) -> int:
    """Reverse ``width`` bits from ``index``."""
    if width < 0:
        raise ValueError("width must be non-negative")

    reversed_bits = 0
    for _ in range(width):
        reversed_bits = (reversed_bits << 1) | (index & 1)
        index >>= 1
    return reversed_bits


def bit_reversed_order(values: Sequence[int]) -> list[int]:
    """Return the array reordered by bit-reversed indices."""
    length = len(values)
    if length == 0:
        return []
    if length & (length - 1):
        raise ValueError("bit_reversed_order requires a power-of-two length")

    width = length.bit_length() - 1
    return [values[bit_reverse(index, width)] for index in range(length)]

