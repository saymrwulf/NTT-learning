from __future__ import annotations

import unittest

import ipywidgets as widgets

from ntt_learning.visuals import _convolution_frame_html, schoolbook_diagonal_player


class VisualUxTests(unittest.TestCase):
    def test_schoolbook_frame_uses_responsive_html_layout(self) -> None:
        html = _convolution_frame_html(
            [1, 2, 3, 4],
            [5, 6, 7, 8],
            diagonal_index=2,
            title="Schoolbook multiplication as a moving diagonal",
        )
        compact = html.replace(" ", "")

        self.assertIn("overflow-x:auto", html)
        self.assertIn("display:grid", compact)
        self.assertIn("grid-template-columns:72pxminmax(74px,1fr)", compact)
        self.assertIn("Active diagonal: y2", html)
        self.assertIn("Output coefficients after this sweep", html)
        self.assertNotIn("<svg", html)

    def test_schoolbook_player_updates_when_slider_moves(self) -> None:
        player = schoolbook_diagonal_player([1, 2, 3, 4], [5, 6, 7, 8])

        self.assertIsInstance(player, widgets.VBox)
        self.assertEqual(player.layout.width, "100%")

        content = player.children[1]
        controls = content.children[0]
        slider = controls.children[1]
        frame_html = content.children[1]
        caption_html = content.children[2]

        self.assertIsInstance(slider, widgets.IntSlider)
        self.assertEqual(slider.layout.width, "100%")
        self.assertIn("Active diagonal: y0", frame_html.value)

        slider.value = 3

        self.assertIn("Active diagonal: y3", frame_html.value)
        self.assertIn("Frame 4 of", caption_html.value)


if __name__ == "__main__":
    unittest.main()
