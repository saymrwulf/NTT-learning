from __future__ import annotations

import os
import unittest

import ipywidgets as widgets

from ntt_learning.course import REPO_ROOT

MPLCONFIGDIR = REPO_ROOT / ".cache" / "matplotlib"
MPLCONFIGDIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPLCONFIGDIR))

from ntt_learning.toy_ntt import fast_ntt_psi_ct_trace, find_psi
from ntt_learning.visuals import (
    _convolution_frame_html,
    butterfly_story_player,
    direct_ntt_player,
    schoolbook_diagonal_player,
    wraparound_comparison_player,
)


def player_parts(player: widgets.Widget) -> tuple[widgets.IntSlider, widgets.HTML, widgets.HTML]:
    content = player.children[1]
    controls = content.children[0]
    slider = controls.children[1]
    frame_html = content.children[1]
    caption_html = content.children[2]
    return slider, frame_html, caption_html


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

        slider, frame_html, caption_html = player_parts(player)

        self.assertIsInstance(slider, widgets.IntSlider)
        self.assertEqual(slider.layout.width, "100%")
        self.assertIn("Active diagonal: y0", frame_html.value)

        slider.value = 3

        self.assertIn("Active diagonal: y3", frame_html.value)
        self.assertIn("Frame 4 of", caption_html.value)

    def test_svg_players_render_in_scrollable_non_shrinking_frames(self) -> None:
        psi = find_psi(order=4, modulus=17)
        trace = fast_ntt_psi_ct_trace([1, 2, 3, 4], modulus=17, psi=psi)
        players = [
            wraparound_comparison_player([3, 0, 2, 1, 5, 4, 6], n=4),
            direct_ntt_player([1, 2, 3, 4], modulus=17, psi=psi),
            butterfly_story_player(trace),
        ]

        for player in players:
            slider, frame_html, _ = player_parts(player)
            self.assertIsInstance(slider, widgets.IntSlider)
            self.assertIn("overflow-x:auto", frame_html.value)
            self.assertIn("<svg", frame_html.value)
            self.assertIn("max-width:none", frame_html.value)
            self.assertIn("min-width:", frame_html.value)
            self.assertNotIn('width="100%"', frame_html.value)

    def test_svg_players_advance_cleanly_when_slider_moves(self) -> None:
        psi = find_psi(order=4, modulus=17)
        trace = fast_ntt_psi_ct_trace([1, 2, 3, 4], modulus=17, psi=psi)
        players = [
            wraparound_comparison_player([3, 0, 2, 1, 5, 4, 6], n=4),
            direct_ntt_player([1, 2, 3, 4], modulus=17, psi=psi),
            butterfly_story_player(trace),
        ]

        for player in players:
            slider, frame_html, caption_html = player_parts(player)
            before = frame_html.value
            slider.value = 1
            self.assertNotEqual(before, frame_html.value)
            self.assertIn("Frame 2 of", caption_html.value)


if __name__ == "__main__":
    unittest.main()
