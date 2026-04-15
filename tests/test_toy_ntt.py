from __future__ import annotations

import unittest

from ntt_learning.toy_ntt import (
    apply_ct_stage,
    bit_reverse,
    bit_reversed_order,
    ct_butterfly_pair,
    find_primitive_root,
    forward_ntt,
    inverse_ntt,
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


if __name__ == "__main__":
    unittest.main()
