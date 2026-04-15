"""Small, inspectable helpers for the NTT learning course."""

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


def pairwise_product_grid(left: Sequence[int], right: Sequence[int]) -> list[list[int]]:
    """Return the full schoolbook multiplication grid."""
    return [[int(left_value * right_value) for right_value in right] for left_value in left]


def convolution_contributions(left: Sequence[int], right: Sequence[int]) -> list[dict[str, object]]:
    """Return each output index and the contributing schoolbook products."""
    raw = schoolbook_convolution(left, right)
    rows: list[dict[str, object]] = []
    for output_index, total in enumerate(raw):
        terms = []
        for left_index, left_value in enumerate(left):
            right_index = output_index - left_index
            if right_index < 0 or right_index >= len(right):
                continue
            right_value = right[right_index]
            terms.append(
                {
                    "left_index": left_index,
                    "right_index": right_index,
                    "left_value": int(left_value),
                    "right_value": int(right_value),
                    "product": int(left_value * right_value),
                }
            )
        rows.append({"output_index": output_index, "terms": terms, "total": int(total)})
    return rows


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


def wraparound_contributions(
    coefficients: Sequence[int], n: int, negacyclic: bool = True
) -> list[dict[str, object]]:
    """Describe how high-degree terms fold back into degree < n."""
    if n <= 0:
        raise ValueError("n must be positive")

    reduced = [0] * n
    rows: list[list[dict[str, int]]] = [[] for _ in range(n)]
    for index, coefficient in enumerate(coefficients):
        wraps, slot = divmod(index, n)
        sign = -1 if negacyclic and wraps % 2 else 1
        signed_value = int(sign * coefficient)
        reduced[slot] += signed_value
        rows[slot].append(
            {
                "source_index": index,
                "wraps": wraps,
                "sign": sign,
                "value": int(coefficient),
                "signed_value": signed_value,
            }
        )

    return [
        {"slot": slot, "contributions": rows[slot], "total": int(reduced[slot])}
        for slot in range(n)
    ]


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


def pointwise_multiply(
    left: Sequence[int], right: Sequence[int], modulus: int | None = None
) -> list[int]:
    """Multiply transform-domain entries slot by slot."""
    if len(left) != len(right):
        raise ValueError("left and right must have the same length")
    products = [int(a * b) for a, b in zip(left, right)]
    return _apply_mod(products, modulus)


def scale_values(values: Sequence[int], factor: int, modulus: int | None = None) -> list[int]:
    """Multiply all values by a scalar."""
    scaled = [int(factor * value) for value in values]
    return _apply_mod(scaled, modulus)


def base_multiply_pair(
    left: Sequence[int], right: Sequence[int], zeta: int, modulus: int
) -> list[int]:
    """Multiply two degree-1 polynomials in a quadratic factor ring."""
    if len(left) != 2 or len(right) != 2:
        raise ValueError("base_multiply_pair expects two 2-term coefficient vectors")
    a0, a1 = (int(left[0]), int(left[1]))
    b0, b1 = (int(right[0]), int(right[1]))
    return [
        (a0 * b0 + zeta * a1 * b1) % modulus,
        (a0 * b1 + a1 * b0) % modulus,
    ]


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


def find_psi(order: int, modulus: int) -> int:
    """Find a primitive ``2 * order``-th root for negative-wrapped NTT."""
    full_order = 2 * order
    root = find_primitive_root(full_order, modulus)
    if pow(root, order, modulus) != (modulus - 1) % modulus:
        raise ValueError(f"primitive {full_order}-th root does not satisfy psi^order = -1")
    return root


def forward_ntt(values: Sequence[int], modulus: int, omega: int) -> list[int]:
    """Definition-first positive-wrapped NTT using the matrix viewpoint."""
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


def ntt_psi_exponent_grid(length: int) -> list[list[int]]:
    """Return the exponent grid used by direct negative-wrapped NTT."""
    return [[2 * row * column + row for row in range(length)] for column in range(length)]


def ntt_psi_matrix(length: int, modulus: int, psi: int) -> list[list[int]]:
    """Return the direct negative-wrapped transform matrix."""
    return [
        [pow(psi, 2 * row * column + row, modulus) for row in range(length)]
        for column in range(length)
    ]


def forward_ntt_psi(values: Sequence[int], modulus: int, psi: int) -> list[int]:
    """Definition-first negative-wrapped NTT using a 2n-th root ``psi``."""
    n = len(values)
    if n == 0:
        return []

    spectrum = []
    for column in range(n):
        total = 0
        for row, value in enumerate(values):
            total += value * pow(psi, 2 * row * column + row, modulus)
        spectrum.append(total % modulus)
    return spectrum


def inverse_ntt_psi(values: Sequence[int], modulus: int, psi: int) -> list[int]:
    """Inverse of ``forward_ntt_psi``."""
    n = len(values)
    if n == 0:
        return []

    n_inverse = mod_inverse(n, modulus)
    recovered = []
    for row in range(n):
        total = 0
        for column, value in enumerate(values):
            total += value * pow(psi, -(2 * row * column + row), modulus)
        recovered.append((n_inverse * total) % modulus)
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


@dataclass(frozen=True)
class TransformStage:
    """One visualizable stage in a fast NTT / iNTT trace."""

    algorithm: str
    stage_index: int
    input_values: tuple[int, ...]
    output_values: tuple[int, ...]
    pairings: tuple[tuple[int, int], ...]
    zetas: tuple[int, ...]
    note: str


@dataclass(frozen=True)
class TransformTrace:
    """A full fast-transform trace suitable for notebook visualization."""

    algorithm: str
    modulus: int
    root: int
    input_values: tuple[int, ...]
    stages: tuple[TransformStage, ...]
    raw_output: tuple[int, ...]
    normal_order_output: tuple[int, ...]
    scaled_output: tuple[int, ...] | None = None


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


def stage_rows(stage: TransformStage) -> list[dict[str, object]]:
    """Return rows describing the pair operations of one trace stage."""
    rows = []
    for pair, zeta in zip(stage.pairings, stage.zetas):
        left, right = pair
        rows.append(
            {
                "pair": pair,
                "zeta": zeta,
                "inputs": (stage.input_values[left], stage.input_values[right]),
                "outputs": (stage.output_values[left], stage.output_values[right]),
            }
        )
    return rows


def bit_reverse(index: int, width: int) -> int:
    """Reverse ``width`` bits from ``index``."""
    if width < 0:
        raise ValueError("width must be non-negative")

    reversed_bits = 0
    for _ in range(width):
        reversed_bits = (reversed_bits << 1) | (index & 1)
        index >>= 1
    return reversed_bits


def bit_reversed_indices(length: int) -> list[int]:
    """Return the bit-reversal permutation for ``length``."""
    if length <= 0:
        raise ValueError("length must be positive")
    if length & (length - 1):
        raise ValueError("bit_reversed_indices requires a power-of-two length")

    width = length.bit_length() - 1
    return [bit_reverse(index, width) for index in range(length)]


def bit_reversed_order(values: Sequence[int]) -> list[int]:
    """Return the array reordered by bit-reversed indices."""
    length = len(values)
    if length == 0:
        return []
    permutation = bit_reversed_indices(length)
    return [values[index] for index in permutation]


def _interleave(left: Sequence[int], right: Sequence[int]) -> list[int]:
    result: list[int] = []
    for left_value, right_value in zip(left, right):
        result.extend([int(left_value), int(right_value)])
    return result


def _renumber_stages(stages: Sequence[TransformStage]) -> tuple[TransformStage, ...]:
    return tuple(
        TransformStage(
            algorithm=stage.algorithm,
            stage_index=index + 1,
            input_values=stage.input_values,
            output_values=stage.output_values,
            pairings=stage.pairings,
            zetas=stage.zetas,
            note=stage.note,
        )
        for index, stage in enumerate(stages)
    )


def _merge_child_stages(
    left_stages: Sequence[TransformStage], right_stages: Sequence[TransformStage]
) -> list[TransformStage]:
    if len(left_stages) != len(right_stages):
        raise ValueError("expected the same number of stages on both recursive branches")

    merged: list[TransformStage] = []
    for left_stage, right_stage in zip(left_stages, right_stages):
        merged.append(
            TransformStage(
                algorithm=left_stage.algorithm,
                stage_index=0,
                input_values=tuple(_interleave(left_stage.input_values, right_stage.input_values)),
                output_values=tuple(_interleave(left_stage.output_values, right_stage.output_values)),
                pairings=tuple((2 * a, 2 * b) for a, b in left_stage.pairings)
                + tuple((2 * a + 1, 2 * b + 1) for a, b in right_stage.pairings),
                zetas=left_stage.zetas + right_stage.zetas,
                note=left_stage.note,
            )
        )
    return merged


def _fast_ntt_psi_ct_recursive(
    values: Sequence[int], modulus: int, psi: int
) -> tuple[tuple[int, ...], list[TransformStage]]:
    size = len(values)
    if size == 1:
        return (int(values[0]),), []

    even_output, even_stages = _fast_ntt_psi_ct_recursive(values[0::2], modulus, pow(psi, 2, modulus))
    odd_output, odd_stages = _fast_ntt_psi_ct_recursive(values[1::2], modulus, pow(psi, 2, modulus))

    merged_stages = _merge_child_stages(even_stages, odd_stages)
    stage_input = tuple(_interleave(even_output, odd_output))

    output = list(stage_input)
    pairings = []
    zetas = []
    for column in range(size // 2):
        left = 2 * column
        right = 2 * column + 1
        zeta = pow(psi, 2 * column + 1, modulus)
        output[left], output[right] = ct_butterfly_pair(stage_input[left], stage_input[right], zeta, modulus)
        pairings.append((left, right))
        zetas.append(zeta)

    merged_stages.append(
        TransformStage(
            algorithm="ct",
            stage_index=0,
            input_values=stage_input,
            output_values=tuple(output),
            pairings=tuple(pairings),
            zetas=tuple(zetas),
            note="Interleave recursive sub-transforms, then apply adjacent CT butterflies.",
        )
    )
    return tuple(output), merged_stages


def fast_ntt_psi_ct_trace(values: Sequence[int], modulus: int, psi: int) -> TransformTrace:
    """Return a stage-by-stage CT fast-NTT trace with BO output and NO comparison."""
    if not values:
        return TransformTrace("ct", modulus, psi, (), (), (), (), None)
    if len(values) & (len(values) - 1):
        raise ValueError("fast_ntt_psi_ct_trace requires a power-of-two length")

    raw_output, stages = _fast_ntt_psi_ct_recursive(values, modulus, psi)
    return TransformTrace(
        algorithm="ct",
        modulus=modulus,
        root=psi,
        input_values=tuple(int(value) for value in values),
        stages=_renumber_stages(stages),
        raw_output=raw_output,
        normal_order_output=tuple(bit_reversed_order(raw_output)),
        scaled_output=None,
    )


def fast_ntt_psi_ct(values: Sequence[int], modulus: int, psi: int) -> list[int]:
    """Compute the BO output of the CT fast negative-wrapped NTT."""
    return list(fast_ntt_psi_ct_trace(values, modulus, psi).raw_output)


def _fast_intt_psi_gs_recursive(
    values: Sequence[int], modulus: int, psi: int
) -> tuple[tuple[int, ...], list[TransformStage]]:
    size = len(values)
    if size == 1:
        return (int(values[0]),), []

    stage_input = tuple(int(value) for value in values)
    stage_output = list(stage_input)
    pairings = []
    zetas = []
    for column in range(size // 2):
        left = 2 * column
        right = 2 * column + 1
        zeta = mod_inverse(pow(psi, 2 * column + 1, modulus), modulus)
        stage_output[left], stage_output[right] = gs_butterfly_pair(
            stage_input[left], stage_input[right], zeta, modulus
        )
        pairings.append((left, right))
        zetas.append(zeta)

    even_output, even_stages = _fast_intt_psi_gs_recursive(
        stage_output[0::2], modulus, pow(psi, 2, modulus)
    )
    odd_output, odd_stages = _fast_intt_psi_gs_recursive(
        stage_output[1::2], modulus, pow(psi, 2, modulus)
    )

    return (
        tuple(_interleave(even_output, odd_output)),
        [
            TransformStage(
                algorithm="gs",
                stage_index=0,
                input_values=stage_input,
                output_values=tuple(stage_output),
                pairings=tuple(pairings),
                zetas=tuple(zetas),
                note="Apply adjacent GS butterflies, then recurse on even and odd branches.",
            ),
            *_merge_child_stages(even_stages, odd_stages),
        ],
    )


def fast_intt_psi_gs_trace(values: Sequence[int], modulus: int, psi: int) -> TransformTrace:
    """Return a stage-by-stage GS fast-iNTT trace from BO input to NO output."""
    if not values:
        return TransformTrace("gs", modulus, psi, (), (), (), (), ())
    if len(values) & (len(values) - 1):
        raise ValueError("fast_intt_psi_gs_trace requires a power-of-two length")

    raw_output, stages = _fast_intt_psi_gs_recursive(values, modulus, psi)
    n_inverse = mod_inverse(len(values), modulus)
    scaled_output = tuple((n_inverse * value) % modulus for value in raw_output)
    return TransformTrace(
        algorithm="gs",
        modulus=modulus,
        root=psi,
        input_values=tuple(int(value) for value in values),
        stages=_renumber_stages(stages),
        raw_output=raw_output,
        normal_order_output=raw_output,
        scaled_output=scaled_output,
    )


def fast_intt_psi_gs(values: Sequence[int], modulus: int, psi: int) -> list[int]:
    """Compute the NO output of the GS fast negative-wrapped inverse NTT."""
    trace = fast_intt_psi_gs_trace(values, modulus, psi)
    return list(trace.scaled_output or ())
