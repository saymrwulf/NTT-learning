from __future__ import annotations

import unittest

from ntt_learning.toy_ntt import (
    apply_ct_stage,
    base_multiply_pair,
    bit_reverse,
    bit_reversed_indices,
    bit_reversed_order,
    ct_butterfly_pair,
    fast_intt_psi_gs,
    fast_intt_psi_gs_trace,
    fast_ntt_psi_ct,
    fast_ntt_psi_ct_trace,
    find_psi,
    find_primitive_root,
    forward_ntt,
    forward_ntt_psi,
    inverse_ntt,
    inverse_ntt_psi,
    negacyclic_multiply,
    negacyclic_reduce,
    schoolbook_convolution,
    stage_pairings,
)


class ToyNttTests(unittest.TestCase):
    def test_schoolbook_convolution(self) -> None:
        self.assertEqual(schoolbook_convolution([1, 2], [3, 4]), [3, 10, 8])

    def test_negacyclic_reduce(self) -> None:
        self.assertEqual(negacyclic_reduce([1, 2, 3, 4, 5], n=4), [-4, 2, 3, 4])

    def test_negacyclic_multiply(self) -> None:
        self.assertEqual(
            negacyclic_multiply([1, 0, 0, 1], [1, 0, 0, 1], n=4),
            [1, 0, -1, 2],
        )

    def test_forward_inverse_round_trip(self) -> None:
        signal = [3, 1, 4, 1]
        omega = find_primitive_root(order=4, modulus=17)
        spectrum = forward_ntt(signal, modulus=17, omega=omega)
        self.assertEqual(inverse_ntt(spectrum, modulus=17, omega=omega), signal)

    def test_ct_butterfly_pair(self) -> None:
        self.assertEqual(ct_butterfly_pair(7, 5, 3, 17), (5, 9))

    def test_stage_pairings(self) -> None:
        self.assertEqual(stage_pairings(length=8, block_size=4), [(0, 2), (1, 3), (4, 6), (5, 7)])

    def test_apply_ct_stage(self) -> None:
        stage_output, _ = apply_ct_stage([1, 2, 3, 4], block_size=2, zetas=1, modulus=17)
        self.assertEqual(stage_output, [3, 16, 7, 16])

    def test_bit_reverse(self) -> None:
        self.assertEqual(bit_reverse(0b101, width=3), 0b101)
        self.assertEqual(bit_reverse(0b011, width=3), 0b110)

    def test_bit_reversed_order(self) -> None:
        self.assertEqual(bit_reversed_order(list(range(8))), [0, 4, 2, 6, 1, 5, 3, 7])

    def test_bit_reversed_indices(self) -> None:
        self.assertEqual(bit_reversed_indices(8), [0, 4, 2, 6, 1, 5, 3, 7])

    def test_find_psi(self) -> None:
        self.assertEqual(find_psi(order=4, modulus=17), 2)

    def test_forward_inverse_ntt_psi_round_trip(self) -> None:
        signal = [6, 0, 5, 2]
        psi = find_psi(order=4, modulus=17)
        spectrum = forward_ntt_psi(signal, modulus=17, psi=psi)
        self.assertEqual(inverse_ntt_psi(spectrum, modulus=17, psi=psi), signal)

    def test_fast_ct_trace_matches_paper_example(self) -> None:
        trace = fast_ntt_psi_ct_trace([1, 2, 3, 4], modulus=7681, psi=1925)
        self.assertEqual(list(trace.raw_output), [1467, 3471, 2807, 7621])
        self.assertEqual(list(trace.normal_order_output), [1467, 2807, 3471, 7621])

    def test_fast_gs_trace_matches_paper_example(self) -> None:
        trace = fast_intt_psi_gs_trace([1467, 3471, 2807, 7621], modulus=7681, psi=1925)
        self.assertEqual(list(trace.raw_output), [4, 8, 12, 16])
        self.assertEqual(list(trace.scaled_output or ()), [1, 2, 3, 4])

    def test_fast_ct_and_gs_round_trip(self) -> None:
        signal = [3, 1, 4, 1]
        psi = find_psi(order=4, modulus=17)
        bo_spectrum = fast_ntt_psi_ct(signal, modulus=17, psi=psi)
        self.assertEqual(fast_intt_psi_gs(bo_spectrum, modulus=17, psi=psi), signal)

    def test_base_multiply_pair(self) -> None:
        self.assertEqual(base_multiply_pair([1, 2], [3, 4], zeta=5, modulus=17), [9, 10])


if __name__ == "__main__":
    unittest.main()
