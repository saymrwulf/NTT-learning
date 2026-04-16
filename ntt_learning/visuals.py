"""Blunt visual helpers for the NTT notebooks."""

from __future__ import annotations

from html import escape
from typing import Sequence

import ipywidgets as widgets
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from IPython.display import clear_output, display

from .toy_ntt import (
    TransformStage,
    TransformTrace,
    base_multiply_pair,
    bit_reversed_order,
    convolution_contributions,
    forward_ntt_psi,
    inverse_ntt_psi,
    ntt_psi_exponent_grid,
    ntt_psi_matrix,
    pairwise_product_grid,
    pointwise_multiply,
    stage_pairings,
    wraparound_contributions,
)

SVG_BG = "#f7f3ea"
SVG_PANEL = "#fffdf8"
SVG_INK = "#1f2933"
SVG_SOFT = "#d8e2dc"
SVG_ACCENT = "#ef476f"
SVG_HILITE = "#ffd166"
SVG_GOOD = "#06d6a0"
SVG_WARN = "#f08a5d"
SVG_BLUE = "#118ab2"


def _full_width_layout(**overrides: str) -> widgets.Layout:
    settings = {
        "width": "100%",
        "max_width": "100%",
    }
    settings.update(overrides)
    return widgets.Layout(**settings)


def _widget_chrome(title: str, subtitle: str, view: widgets.Widget) -> widgets.Widget:
    header = widgets.HTML(
        f"""
        <div style="
            width: 100%;
            box-sizing: border-box;
            background: linear-gradient(135deg, #f7ede2 0%, #f5cac3 45%, #84a59d 100%);
            color: #102a43;
            padding: 14px 16px;
            border-radius: 14px 14px 0 0;
            font-family: 'Avenir Next', 'Trebuchet MS', sans-serif;
            box-shadow: inset 0 0 0 1px rgba(16,42,67,0.12);
        ">
          <div style="font-size: 18px; font-weight: 800;">{escape(title)}</div>
          <div style="font-size: 12px; margin-top: 4px;">{escape(subtitle)}</div>
        </div>
        """
        ,
        layout=_full_width_layout(min_width="0"),
    )
    view.layout = _full_width_layout(min_width="0")
    box = widgets.VBox(
        [header, view],
        layout=_full_width_layout(min_width="0", border="1px solid #d9d9d9", overflow="hidden", align_items="stretch"),
    )
    return box


def _player_widget(
    *,
    title: str,
    subtitle: str,
    frames: Sequence[str],
    captions: Sequence[str],
    width: str = "100%",
) -> widgets.Widget:
    if not frames:
        raise ValueError("player widget requires at least one frame")

    play = widgets.Play(value=0, min=0, max=len(frames) - 1, step=1, interval=1100, description="Play")
    slider = widgets.IntSlider(
        value=0,
        min=0,
        max=len(frames) - 1,
        step=1,
        description="Step",
        continuous_update=False,
        layout=_full_width_layout(min_width="0", flex="1 1 auto"),
    )
    widgets.jslink((play, "value"), (slider, "value"))

    play.layout = widgets.Layout(width="auto")
    frame_html = widgets.HTML(layout=_full_width_layout(min_width="0", overflow="hidden"))
    caption_html = widgets.HTML(layout=_full_width_layout(min_width="0"))

    def render(index: int) -> None:
        frame_html.value = f"""
        <div style="width:100%; max-width:100%; overflow-x:auto; overflow-y:hidden; background:#fff9f2; padding: 10px 14px 14px 14px; box-sizing:border-box;">
          {frames[index]}
        </div>
        """
        caption_html.value = f"""
        <div style="
            background: #fffdf8;
            border-top: 1px solid #e8dcc9;
            padding: 12px 16px;
            font-family: 'Avenir Next', 'Trebuchet MS', sans-serif;
            color: #243b53;
            font-size: 13px;
            line-height: 1.45;
        ">
          <strong>Frame {index + 1} of {len(frames)}</strong><br>
          {escape(captions[index])}
        </div>
        """

    slider.observe(lambda change: render(change["new"]), names="value")
    render(0)

    controls = widgets.VBox(
        [
            play,
            slider,
        ],
        layout=_full_width_layout(min_width="0", padding="10px 14px", align_items="stretch"),
    )
    content = widgets.VBox(
        [controls, frame_html, caption_html],
        layout=_full_width_layout(min_width="0", align_items="stretch"),
    )
    return _widget_chrome(title, subtitle, content)


def _svg_box(x: float, y: float, w: float, h: float, label: str, value: str, *, fill: str, stroke: str, stroke_width: float = 2.0) -> str:
    return f"""
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"></rect>
    <text x="{x + w / 2}" y="{y + 18}" text-anchor="middle" font-size="11" font-family="Menlo, monospace" fill="{SVG_INK}">{escape(label)}</text>
    <text x="{x + w / 2}" y="{y + h / 2 + 10}" text-anchor="middle" font-size="22" font-weight="700" font-family="Menlo, monospace" fill="{SVG_INK}">{escape(value)}</text>
    """


def _svg_text(x: float, y: float, text: str, *, size: int = 14, weight: str = "400", fill: str = SVG_INK, anchor: str = "start") -> str:
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" font-weight="{weight}" font-family="Avenir Next, Trebuchet MS, sans-serif" fill="{fill}">{escape(text)}</text>'


def _svg_multiline_text(
    x: float,
    y: float,
    text: str,
    *,
    max_chars: int = 42,
    line_height: int = 16,
    size: int = 14,
    weight: str = "400",
    fill: str = SVG_INK,
    anchor: str = "start",
) -> str:
    words = text.split()
    if not words:
        return ""

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)

    return "".join(
        _svg_text(
            x,
            y + index * line_height,
            line,
            size=size,
            weight=weight,
            fill=fill,
            anchor=anchor,
        )
        for index, line in enumerate(lines)
    )


def _svg_canvas_open(width: int, height: int) -> str:
    return (
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'preserveAspectRatio="xMinYMin meet" '
        f'style="display:block;width:{width}px;max-width:none;min-width:{width}px;height:auto;background:{SVG_BG}; border-radius:0 0 14px 14px;">'
    )


def _html_token(label: str, value: str, *, fill: str, border: str, text: str = SVG_INK) -> str:
    return f"""
    <div style="
        min-width: 56px;
        padding: 8px 10px;
        border-radius: 12px;
        border: 2px solid {border};
        background: {fill};
        color: {text};
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 3px;
        text-align: center;
    ">
      <div style="font-size: 11px; font-weight: 700; letter-spacing: 0.03em; text-transform: uppercase;">{escape(label)}</div>
      <div style="font-size: 19px; font-weight: 800; font-family: Menlo, monospace;">{escape(value)}</div>
    </div>
    """


def _convolution_frame_html(
    left: Sequence[int],
    right: Sequence[int],
    diagonal_index: int,
    *,
    title: str,
) -> str:
    rows = convolution_contributions(left, right)
    current = rows[diagonal_index]
    grid = pairwise_product_grid(left, right)
    terms = current["terms"]
    grid_columns = "72px " + " ".join(["minmax(74px, 1fr)"] * len(right))
    output_columns = " ".join(["minmax(70px, 1fr)"] * len(rows))

    product_cells = []
    for column_index, value in enumerate(right):
        product_cells.append(
            f"""
            <div style="padding:8px 6px; text-align:center; font-size:12px; font-weight:800; color:#486581;">
              b{column_index} = <span style="font-family: Menlo, monospace; color:{SVG_INK};">{value}</span>
            </div>
            """
        )

    for row_index, row_values in enumerate(grid):
        product_cells.append(
            f"""
            <div style="padding:8px 6px; text-align:center; font-size:12px; font-weight:800; color:#486581;">
              a{row_index} = <span style="font-family: Menlo, monospace; color:{SVG_INK};">{left[row_index]}</span>
            </div>
            """
        )
        for column_index, value in enumerate(row_values):
            active = row_index + column_index == diagonal_index
            done = row_index + column_index < diagonal_index
            fill = SVG_HILITE if active else "#e6fffa" if done else "#f8f9fa"
            border = SVG_ACCENT if active else SVG_GOOD if done else "#cbd2d9"
            product_cells.append(
                _html_token(
                    f"a{row_index}·b{column_index}",
                    str(value),
                    fill=fill,
                    border=border,
                )
            )

    output_cells = []
    for row in rows:
        output_index = int(row["output_index"])
        fill = SVG_HILITE if output_index == diagonal_index else "#d9f0ff" if output_index < diagonal_index else "#f1f5f9"
        border = SVG_ACCENT if output_index == diagonal_index else SVG_BLUE if output_index < diagonal_index else "#cbd2d9"
        output_cells.append(
            _html_token(
                f"y{output_index}",
                str(row["total"]),
                fill=fill,
                border=border,
            )
        )

    equation_chips = []
    for term in terms:
        equation_chips.append(
            f"""
            <div style="
                padding: 8px 10px;
                border-radius: 999px;
                background: #fff7d6;
                border: 1px solid #f2c94c;
                font-family: Menlo, monospace;
                font-size: 13px;
                font-weight: 700;
                color: {SVG_INK};
            ">
              {term["left_value"]} x {term["right_value"]} = {term["product"]}
            </div>
            """
        )
    equation = " + ".join(
        f"{term['left_value']}x{term['right_value']}={term['product']}"
        for term in terms
    ) or "0"

    return f"""
    <div style="
        width: 100%;
        max-width: 100%;
        box-sizing: border-box;
        display: grid;
        gap: 14px;
        font-family: 'Avenir Next', 'Trebuchet MS', sans-serif;
        color: {SVG_INK};
    ">
      <div style="
          display:flex;
          flex-wrap:wrap;
          gap:10px;
          align-items:center;
      ">
        <div style="
            padding:10px 12px;
            border-radius:14px;
            background:#fff3cd;
            border:2px solid #f2c94c;
            font-size:15px;
            font-weight:800;
        ">
          Active diagonal: y{diagonal_index}
        </div>
        <div style="
            padding:10px 12px;
            border-radius:14px;
            background:#eef6ff;
            border:1px solid #bcd4f6;
            font-size:13px;
            color:#334e68;
        ">
          Highlight every cell where row index + column index = {diagonal_index}
        </div>
      </div>

      <div style="
          display:flex;
          flex-wrap:wrap;
          gap:8px;
          align-items:center;
      ">
        <div style="font-size:12px; font-weight:800; color:#486581;">Left polynomial</div>
        {"".join(_html_token(f"a{i}", str(value), fill="#edf6f9", border="#8ecae6") for i, value in enumerate(left))}
      </div>

      <div style="
          display:flex;
          flex-wrap:wrap;
          gap:8px;
          align-items:center;
      ">
        <div style="font-size:12px; font-weight:800; color:#486581;">Right polynomial</div>
        {"".join(_html_token(f"b{i}", str(value), fill="#fef6e4", border="#f6bd60") for i, value in enumerate(right))}
      </div>

      <div style="
          padding:14px;
          border-radius:18px;
          background:{SVG_PANEL};
          border:1px solid #e8dcc9;
          box-shadow: inset 0 0 0 1px rgba(255,255,255,0.6);
      ">
        <div style="font-size:16px; font-weight:800; margin-bottom:10px;">{escape(title)}</div>
        <div style="font-size:13px; color:#486581; margin-bottom:12px;">
          Each highlighted product belongs to the same output coefficient.
        </div>
        <div style="overflow-x:auto; padding-bottom:4px;">
          <div style="
              display:grid;
              grid-template-columns:{grid_columns};
              gap:8px;
              align-items:stretch;
              min-width:max-content;
          ">
            <div></div>
            {"".join(product_cells)}
          </div>
        </div>
      </div>

      <div style="
          padding:14px;
          border-radius:18px;
          background:#f8fbff;
          border:1px solid #d6e4f0;
      ">
        <div style="font-size:16px; font-weight:800; margin-bottom:10px;">Output coefficients after this sweep</div>
        <div style="display:grid; grid-template-columns:{output_columns}; gap:8px;">
          {"".join(output_cells)}
        </div>
      </div>

      <div style="
          padding:14px;
          border-radius:18px;
          background:#fffdf8;
          border:1px solid #ecdcc5;
      ">
        <div style="font-size:16px; font-weight:800; margin-bottom:10px;">Current diagonal terms</div>
        <div style="display:flex; flex-wrap:wrap; gap:8px; margin-bottom:12px;">
          {"".join(equation_chips) or '<div style="font-size:13px; color:#486581;">No terms yet.</div>'}
        </div>
        <div style="
            padding:12px 14px;
            border-radius:14px;
            background:#102a43;
            color:white;
            font-family: Menlo, monospace;
            font-size:14px;
            font-weight:700;
            overflow-wrap:anywhere;
        ">
          y{diagonal_index} = {escape(equation)} = {current["total"]}
        </div>
      </div>
    </div>
    """


def schoolbook_diagonal_player(left: Sequence[int], right: Sequence[int]) -> widgets.Widget:
    """Interactive diagonal-by-diagonal walkthrough of schoolbook multiplication."""
    rows = convolution_contributions(left, right)
    frames = [
        _convolution_frame_html(left, right, diagonal_index=index, title="Schoolbook multiplication as a moving diagonal")
        for index in range(len(rows))
    ]
    captions = [
        f"Only the highlighted products contribute to y{row['output_index']}. Watch the diagonal sweep across the grid instead of imagining the sum in your head."
        for row in rows
    ]
    return _player_widget(
        title="Convolution Diagonal Player",
        subtitle="Press play. The highlighted diagonal is the coefficient being formed right now.",
        frames=frames,
        captions=captions,
    )


def _wrap_compare_frame_svg(coefficients: Sequence[int], n: int, step: int) -> str:
    cyclic_rows = wraparound_contributions(coefficients, n=n, negacyclic=False)
    negacyclic_rows = wraparound_contributions(coefficients, n=n, negacyclic=True)
    flat = [(index, coefficient) for index, coefficient in enumerate(coefficients)]
    current_index, current_value = flat[step]
    cell = 58
    width = max(980, len(coefficients) * cell + 200)
    height = 450
    top_y = 118
    cyclic_y = 252
    neg_y = 348

    parts = [
        _svg_canvas_open(width, height),
        f'<rect x="18" y="18" width="{width - 36}" height="{height - 36}" rx="18" fill="{SVG_PANEL}" stroke="#e8dcc9" stroke-width="2"></rect>',
        _svg_text(34, 48, "Wraparound Comparison Player", size=22, weight="800"),
        _svg_text(34, 74, f"Current source term: x^{current_index} with coefficient {current_value}", size=13, fill="#486581"),
        _svg_text(34, top_y - 18, "Raw convolution tail", size=14, weight="700"),
        _svg_text(34, cyclic_y - 18, "Cyclic fold into x^n - 1", size=14, weight="700", fill=SVG_BLUE),
        _svg_text(34, neg_y - 18, "Negacyclic fold into x^n + 1", size=14, weight="700", fill=SVG_ACCENT),
    ]

    for index, coefficient in enumerate(coefficients):
        fill = SVG_HILITE if index == current_index else "#f1f5f9" if index > current_index else "#d8f3dc"
        stroke = SVG_ACCENT if index == current_index else "#cbd2d9" if index > current_index else SVG_GOOD
        parts.append(_svg_box(48 + index * cell, top_y, 48, 48, f"x^{index}", str(coefficient), fill=fill, stroke=stroke))

    for slot, row in enumerate(cyclic_rows):
        parts.append(_svg_box(48 + slot * cell, cyclic_y, 48, 48, f"slot {slot}", str(row["total"]), fill="#e0fbfc", stroke=SVG_BLUE))
    for slot, row in enumerate(negacyclic_rows):
        parts.append(_svg_box(48 + slot * cell, neg_y, 48, 48, f"slot {slot}", str(row["total"]), fill="#ffe8d6", stroke=SVG_ACCENT))

    wraps, slot = divmod(current_index, n)
    cyclic_label = f"+ wrap {wraps}"
    neg_label = ("-" if wraps % 2 else "+") + f" wrap {wraps}"
    source_x = 72 + current_index * cell
    target_x = 72 + slot * cell

    parts.append(f'<line x1="{source_x}" y1="{top_y + 48}" x2="{target_x}" y2="{cyclic_y}" stroke="{SVG_BLUE}" stroke-width="4" marker-end="url(#arrow-blue)"></line>')
    parts.append(f'<line x1="{source_x}" y1="{top_y + 48}" x2="{target_x}" y2="{neg_y}" stroke="{SVG_ACCENT}" stroke-width="4" marker-end="url(#arrow-red)"></line>')
    parts.append(f"""
      <defs>
        <marker id="arrow-blue" markerWidth="10" markerHeight="10" refX="7" refY="3" orient="auto">
          <polygon points="0 0, 8 3, 0 6" fill="{SVG_BLUE}"></polygon>
        </marker>
        <marker id="arrow-red" markerWidth="10" markerHeight="10" refX="7" refY="3" orient="auto">
          <polygon points="0 0, 8 3, 0 6" fill="{SVG_ACCENT}"></polygon>
        </marker>
      </defs>
    """)
    parts.append(_svg_text((source_x + target_x) / 2, cyclic_y - 18, cyclic_label, size=12, fill=SVG_BLUE, anchor="middle"))
    parts.append(_svg_text((source_x + target_x) / 2, neg_y - 18, neg_label, size=12, fill=SVG_ACCENT, anchor="middle"))
    parts.append("</svg>")
    return "".join(parts)


def wraparound_comparison_player(coefficients: Sequence[int], n: int) -> widgets.Widget:
    """Interactive comparison of cyclic and negacyclic folding, one source term at a time."""
    frames = [_wrap_compare_frame_svg(coefficients, n, step) for step in range(len(coefficients))]
    captions = []
    for index, coefficient in enumerate(coefficients):
        wraps, slot = divmod(index, n)
        neg_sign = "-" if wraps % 2 else "+"
        captions.append(
            f"x^{index} with coefficient {coefficient} lands in slot {slot}. Cyclic folding keeps a + sign; negacyclic folding uses {neg_sign} after {wraps} wrap(s)."
        )
    return _player_widget(
        title="Wraparound Step Player",
        subtitle="Play one raw coefficient at a time and compare x^n-1 with x^n+1 side by side.",
        frames=frames,
        captions=captions,
    )


def _direct_ntt_frame_svg(values: Sequence[int], modulus: int, psi: int, output_index: int, input_index: int) -> str:
    exponents = ntt_psi_exponent_grid(len(values))
    matrix = ntt_psi_matrix(len(values), modulus, psi)
    cell = 62
    width = 1040
    height = 470
    grid_x = 260
    grid_y = 84
    boxes_y = 360
    contributions = []
    for row, value in enumerate(values):
        exponent = exponents[output_index][row]
        factor = matrix[output_index][row]
        product = (value * factor) % modulus
        contributions.append((exponent, factor, product))

    partial = sum(product for _, _, product in contributions[: input_index + 1]) % modulus
    final = sum(product for _, _, product in contributions) % modulus

    parts = [
        _svg_canvas_open(width, height),
        f'<rect x="18" y="18" width="{width - 36}" height="{height - 36}" rx="18" fill="{SVG_PANEL}" stroke="#e8dcc9" stroke-width="2"></rect>',
        _svg_text(34, 48, "Direct NTTψ Contribution Player", size=22, weight="800"),
        _svg_text(34, 68, f"Building output slot j={output_index}, currently consuming input i={input_index}", size=13, fill="#486581"),
        _svg_text(34, 108, "signal", size=14, weight="700"),
        _svg_text(grid_x, 68, "matrix cell = psi^(2ij + i)", size=14, weight="700"),
    ]

    for index, value in enumerate(values):
        fill = SVG_HILITE if index == input_index else "#d8f3dc" if index < input_index else "#f1f5f9"
        stroke = SVG_ACCENT if index == input_index else SVG_GOOD if index < input_index else "#cbd2d9"
        parts.append(_svg_box(36, 128 + index * 60, 92, 48, f"a{index}", str(value), fill=fill, stroke=stroke))

    for row in range(len(values)):
        parts.append(_svg_text(grid_x - 18, grid_y + row * cell + 34, f"i={row}", size=12, anchor="end"))
    for col in range(len(values)):
        parts.append(_svg_text(grid_x + col * cell + 28, grid_y - 12, f"j={col}", size=12, anchor="middle"))

    for col in range(len(values)):
        for row in range(len(values)):
            active = col == output_index and row == input_index
            done = col == output_index and row < input_index
            fill = SVG_HILITE if active else "#d8f3dc" if done else "#f1f5f9"
            stroke = SVG_ACCENT if active else SVG_GOOD if done else "#cbd2d9"
            parts.append(
                _svg_box(
                    grid_x + col * cell,
                    grid_y + row * cell,
                    56,
                    56,
                    f"{exponents[col][row]}",
                    str(matrix[col][row]),
                    fill=fill,
                    stroke=stroke,
                    stroke_width=3.0 if active else 1.6,
                )
            )

    for index, (_, factor, product) in enumerate(contributions):
        fill = SVG_HILITE if index == input_index else "#d8f3dc" if index < input_index else "#f1f5f9"
        stroke = SVG_ACCENT if index == input_index else SVG_GOOD if index < input_index else "#cbd2d9"
        parts.append(_svg_box(520 + index * 90, boxes_y, 74, 54, f"a{index}·w", str(product), fill=fill, stroke=stroke))
        parts.append(_svg_text(556 + index * 90, boxes_y - 10, f"factor {factor}", size=11, anchor="middle"))

    parts.append(
        _svg_multiline_text(
            34,
            height - 68,
            f"Current partial sum for j={output_index}: {partial} mod {modulus}",
            max_chars=52,
            size=15,
            weight="700",
        )
    )
    parts.append(
        _svg_multiline_text(
            34,
            height - 36,
            f"Completed output slot y{output_index}: {final} mod {modulus}",
            max_chars=52,
            size=15,
            weight="700",
            fill=SVG_ACCENT,
        )
    )
    parts.append("</svg>")
    return "".join(parts)


def direct_ntt_player(values: Sequence[int], modulus: int, psi: int) -> widgets.Widget:
    """Interactive walkthrough of the direct NTT_psi matrix multiplication."""
    frames = []
    captions = []
    for output_index in range(len(values)):
        for input_index in range(len(values)):
            exponent = 2 * input_index * output_index + input_index
            factor = pow(psi, exponent, modulus)
            product = (values[input_index] * factor) % modulus
            frames.append(_direct_ntt_frame_svg(values, modulus, psi, output_index, input_index))
            captions.append(
                f"Output slot j={output_index}: multiply a{input_index}={values[input_index]} by psi^{exponent}={factor} to contribute {product} mod {modulus}."
            )
    return _player_widget(
        title="Direct NTTψ Player",
        subtitle="Press play and watch the transform build one contribution at a time.",
        frames=frames,
        captions=captions,
    )


def _butterfly_story_frame_svg(trace: TransformTrace, stage_index: int, pair_index: int) -> str:
    stage = trace.stages[stage_index]
    left, right = stage.pairings[pair_index]
    zeta = stage.zetas[pair_index]
    width = max(820, len(stage.input_values) * 120)
    height = 340
    input_y = 110
    output_y = 240
    spacing = 92
    start_x = 60
    parts = [
        _svg_canvas_open(width, height),
        f'<rect x="18" y="18" width="{width - 36}" height="{height - 36}" rx="18" fill="{SVG_PANEL}" stroke="#e8dcc9" stroke-width="2"></rect>',
        _svg_text(34, 48, f"{trace.algorithm.upper()} Butterfly Player", size=22, weight="800"),
        _svg_text(34, 68, f"Stage {stage.stage_index}, active pair ({left}, {right}), zeta={zeta}", size=13, fill="#486581"),
    ]

    for index, value in enumerate(stage.input_values):
        active = index in (left, right)
        fill = SVG_HILITE if active else "#f1f5f9"
        stroke = SVG_ACCENT if active else "#cbd2d9"
        parts.append(_svg_box(start_x + index * spacing, input_y, 64, 52, f"in {index}", str(value), fill=fill, stroke=stroke, stroke_width=3.0 if active else 1.8))

    for index, value in enumerate(stage.output_values):
        active = index in (left, right)
        fill = "#d8f3dc" if active else "#f1f5f9"
        stroke = SVG_GOOD if active else "#cbd2d9"
        parts.append(_svg_box(start_x + index * spacing, output_y, 64, 52, f"out {index}", str(value), fill=fill, stroke=stroke, stroke_width=3.0 if active else 1.8))

    for index in range(len(stage.input_values)):
        x = start_x + index * spacing + 32
        color = SVG_ACCENT if index in (left, right) else "#d9d9d9"
        width_line = 4 if index in (left, right) else 1.8
        parts.append(f'<line x1="{x}" y1="{input_y + 52}" x2="{x}" y2="{output_y}" stroke="{color}" stroke-width="{width_line}"></line>')

    x_left = start_x + left * spacing + 32
    x_right = start_x + right * spacing + 32
    parts.append(f'<line x1="{x_left}" y1="{input_y + 62}" x2="{x_right}" y2="{input_y + 62}" stroke="{SVG_ACCENT}" stroke-width="4"></line>')
    parts.append(_svg_text((x_left + x_right) / 2, 196, f"pair ({left}, {right})", size=12, weight="700", fill=SVG_ACCENT, anchor="middle"))
    parts.append(
        _svg_multiline_text(
            (x_left + x_right) / 2,
            214,
            f"inputs -> outputs = ({stage.input_values[left]}, {stage.input_values[right]}) -> ({stage.output_values[left]}, {stage.output_values[right]})",
            max_chars=34,
            line_height=14,
            size=11,
            anchor="middle",
        )
    )
    parts.append(
        _svg_multiline_text(
            (x_left + x_right) / 2,
            242,
            stage.note,
            max_chars=36,
            line_height=14,
            size=11,
            anchor="middle",
            fill="#486581",
        )
    )
    parts.append("</svg>")
    return "".join(parts)


def butterfly_story_player(trace: TransformTrace) -> widgets.Widget:
    """Interactive pair-by-pair walkthrough of a butterfly trace."""
    frames = []
    captions = []
    for stage_index, stage in enumerate(trace.stages):
        for pair_index, pair in enumerate(stage.pairings):
            left, right = pair
            frames.append(_butterfly_story_frame_svg(trace, stage_index, pair_index))
            captions.append(
                f"Stage {stage.stage_index}: the active pair is {pair}. Watch only these two wires. Everything else is parked until its own butterfly fires."
            )
    return _player_widget(
        title="Butterfly Pair Player",
        subtitle="Play pair by pair. This is the local machine the learner needs to internalize.",
        frames=frames,
        captions=captions,
    )


def _value_colors(values: Sequence[int]) -> list[str]:
    colors = []
    for value in values:
        if value < 0:
            colors.append("#f08a5d")
        elif value == 0:
            colors.append("#d9d9d9")
        else:
            colors.append("#7ad3a8")
    return colors


def _draw_value_row(ax, values: Sequence[int], y: float, prefix: str) -> None:
    colors = _value_colors(values)
    for index, (value, color) in enumerate(zip(values, colors)):
        ax.text(
            index,
            y,
            f"{prefix}{index}\n{value}",
            ha="center",
            va="center",
            fontsize=10,
            family="monospace",
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": color,
                "edgecolor": "#222222",
                "linewidth": 1.2,
            },
        )


def _annotate_grid(ax, grid: Sequence[Sequence[int]]) -> None:
    for row, row_values in enumerate(grid):
        for column, value in enumerate(row_values):
            ax.text(
                column,
                row,
                str(value),
                ha="center",
                va="center",
                color="#101010",
                fontsize=10,
                family="monospace",
            )


def plot_integer_grid(
    grid: Sequence[Sequence[int]],
    *,
    title: str,
    x_label: str,
    y_label: str,
    cmap: str = "YlGnBu",
):
    """Plot a heatmap with the exact integer values written in every cell."""
    if not grid or not grid[0]:
        raise ValueError("plot_integer_grid requires a non-empty rectangular grid")

    fig, ax = plt.subplots(figsize=(max(6, len(grid[0]) * 1.2), max(4, len(grid) * 0.85)))
    ax.imshow(grid, cmap=cmap, aspect="auto")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_xticks(range(len(grid[0])))
    ax.set_yticks(range(len(grid)))
    _annotate_grid(ax, grid)
    fig.tight_layout()
    return fig


def plot_convolution_grid(
    left: Sequence[int], right: Sequence[int], title: str = "Schoolbook Product Grid"
):
    """Plot the full schoolbook multiplication table and the diagonal sums."""
    grid = pairwise_product_grid(left, right)
    diagonal_sums = []
    for diagonal in range(len(left) + len(right) - 1):
        total = 0
        for row in range(len(left)):
            column = diagonal - row
            if 0 <= column < len(right):
                total += grid[row][column]
        diagonal_sums.append(total)

    fig, axes = plt.subplots(2, 1, figsize=(max(7, len(right) * 1.2), 6), height_ratios=[3, 1])
    heatmap_ax, sum_ax = axes

    heatmap_ax.imshow(grid, cmap="YlGnBu", aspect="auto")
    heatmap_ax.set_title(title, fontsize=14, fontweight="bold")
    heatmap_ax.set_xlabel("right coefficient index")
    heatmap_ax.set_ylabel("left coefficient index")
    heatmap_ax.set_xticks(range(len(right)))
    heatmap_ax.set_yticks(range(len(left)))

    _annotate_grid(heatmap_ax, grid)

    sum_ax.axis("off")
    sum_ax.set_title("Diagonal Sums = Convolution Coefficients", fontsize=12, fontweight="bold", pad=8)
    for index, value in enumerate(diagonal_sums):
        sum_ax.text(
            index,
            0,
            f"y{index}\n{value}",
            ha="center",
            va="center",
            fontsize=10,
            family="monospace",
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "#f4f1de",
                "edgecolor": "#222222",
                "linewidth": 1.0,
            },
        )
    sum_ax.set_xlim(-0.5, len(diagonal_sums) - 0.5)
    sum_ax.set_ylim(-1, 1)
    fig.tight_layout()
    return fig


def plot_ntt_psi_exponent_heatmap(length: int, title: str = "NTT_psi Exponent Grid"):
    """Plot the exponent pattern 2ij + i used by the direct negative-wrapped NTT."""
    return plot_integer_grid(
        ntt_psi_exponent_grid(length),
        title=title,
        x_label="output index j",
        y_label="input index i",
        cmap="YlOrRd",
    )


def plot_ntt_psi_matrix_heatmap(length: int, modulus: int, psi: int, title: str = "NTT_psi Matrix Values"):
    """Plot the concrete direct transform matrix over Z_q."""
    return plot_integer_grid(
        ntt_psi_matrix(length, modulus, psi),
        title=title,
        x_label="output index j",
        y_label="input index i",
        cmap="PuBuGn",
    )


def plot_wraparound(
    coefficients: Sequence[int],
    n: int,
    *,
    negacyclic: bool = True,
    title: str | None = None,
):
    """Plot how the tail wraps back into degree < n."""
    rows = wraparound_contributions(coefficients, n=n, negacyclic=negacyclic)
    if title is None:
        title = "Negacyclic Folding" if negacyclic else "Cyclic Folding"

    fig, ax = plt.subplots(figsize=(max(8, len(coefficients) * 1.1), 5.5))
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.axis("off")

    top_y = 2.4
    bottom_y = 0.4
    _draw_value_row(ax, coefficients, top_y, "x^")
    reduced_values = [row["total"] for row in rows]
    _draw_value_row(ax, reduced_values, bottom_y, "slot ")

    for slot, row in enumerate(rows):
        for contribution in row["contributions"]:
            source_index = contribution["source_index"]
            color = "#d1495b" if contribution["sign"] < 0 else "#2a9d8f"
            label = "-" if contribution["sign"] < 0 else "+"
            ax.annotate(
                "",
                xy=(slot, bottom_y + 0.3),
                xytext=(source_index, top_y - 0.25),
                arrowprops={"arrowstyle": "->", "color": color, "linewidth": 2.0},
            )
            mid_x = (slot + source_index) / 2
            mid_y = (top_y + bottom_y) / 2 + 0.25
            ax.text(
                mid_x,
                mid_y,
                f"{label} wrap {contribution['wraps']}",
                ha="center",
                va="center",
                fontsize=9,
                color=color,
                family="monospace",
            )

    ax.set_xlim(-0.8, max(len(coefficients), n) - 0.2)
    ax.set_ylim(-0.4, 3.2)
    fig.tight_layout()
    return fig


def plot_vector_comparison(
    left: Sequence[int],
    right: Sequence[int],
    *,
    left_label: str = "left",
    right_label: str = "right",
    title: str = "Vector Comparison",
):
    """Plot two vectors slot-by-slot with explicit differences."""
    if len(left) != len(right):
        raise ValueError("plot_vector_comparison requires equal-length vectors")

    differences = [int(right_value - left_value) for left_value, right_value in zip(left, right)]
    fig, axes = plt.subplots(3, 1, figsize=(max(8, len(left) * 1.3), 7), height_ratios=[1, 1, 1])
    labels = [left_label, right_label, "delta"]
    rows = [left, right, differences]
    row_colors = ["#edf6f9", "#fff3b0", "#f5cac3"]

    for ax, label, values, row_color in zip(axes, labels, rows, row_colors):
        ax.axis("off")
        ax.set_title(label, fontsize=12, fontweight="bold", pad=6)
        for index, value in enumerate(values):
            ax.text(
                index,
                0,
                f"{index}\n{value}",
                ha="center",
                va="center",
                fontsize=10,
                family="monospace",
                bbox={
                    "boxstyle": "round,pad=0.32",
                    "facecolor": row_color if label != "delta" else _value_colors([value])[0],
                    "edgecolor": "#222222",
                    "linewidth": 1.1,
                },
            )
        ax.set_xlim(-0.8, len(values) - 0.2)
        ax.set_ylim(-0.8, 0.8)

    fig.suptitle(title, fontsize=14, fontweight="bold")
    fig.tight_layout()
    return fig


def plot_bit_reversal_mapping(length: int, title: str = "Normal Order To Bit-Reversed Order"):
    """Plot the bit-reversal permutation as explicit wires."""
    if length <= 0 or length & (length - 1):
        raise ValueError("plot_bit_reversal_mapping requires a power-of-two length")

    from .toy_ntt import bit_reversed_indices

    permutation = bit_reversed_indices(length)
    width = length.bit_length() - 1

    fig, ax = plt.subplots(figsize=(8, max(4, length * 0.65)))
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.axis("off")

    for index, target in enumerate(permutation):
        ax.text(
            0,
            -index,
            f"{index:>2} | {index:0{width}b}",
            ha="center",
            va="center",
            family="monospace",
            bbox={"boxstyle": "round,pad=0.25", "facecolor": "#edf6f9", "edgecolor": "#264653"},
        )
        ax.text(
            4,
            -target,
            f"{target:>2} | {target:0{width}b}",
            ha="center",
            va="center",
            family="monospace",
            bbox={"boxstyle": "round,pad=0.25", "facecolor": "#fff3b0", "edgecolor": "#9c6644"},
        )
        ax.plot([0.6, 3.4], [-index, -target], color="#7f5539", linewidth=2.2, alpha=0.9)

    ax.text(0, 1, "NO", ha="center", va="center", fontsize=12, fontweight="bold")
    ax.text(4, 1, "BO", ha="center", va="center", fontsize=12, fontweight="bold")
    ax.set_xlim(-1.2, 5.2)
    ax.set_ylim(-length + 0.2, 1.8)
    fig.tight_layout()
    return fig


def plot_butterfly_network(trace: TransformTrace, title: str | None = None):
    """Plot the whole staged network with pair links visible at each stage."""
    if title is None:
        title = f"{trace.algorithm.upper()} Butterfly Network"

    columns = [trace.input_values] + [stage.output_values for stage in trace.stages]
    fig, ax = plt.subplots(figsize=(max(10, len(columns) * 2.4), max(5, len(trace.input_values) * 0.8)))
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.axis("off")

    x_positions = [index * 2.4 for index in range(len(columns))]

    for column_index, (x, values) in enumerate(zip(x_positions, columns)):
        for row_index, value in enumerate(values):
            ax.text(
                x,
                -row_index,
                str(value),
                ha="center",
                va="center",
                fontsize=10,
                family="monospace",
                bbox={
                    "boxstyle": "round,pad=0.26",
                    "facecolor": _value_colors([value])[0],
                    "edgecolor": "#222222",
                    "linewidth": 1.0,
                },
            )

        label = "input" if column_index == 0 else f"s{column_index}"
        ax.text(x, 1.1, label, ha="center", va="center", fontsize=11, fontweight="bold")

        if column_index == 0:
            continue

        previous_x = x_positions[column_index - 1]
        stage = trace.stages[column_index - 1]
        colors = ["#264653", "#2a9d8f", "#e76f51", "#8d99ae", "#c1121f", "#3a86ff"]

        for index in range(len(values)):
            ax.plot([previous_x + 0.35, x - 0.35], [-index, -index], color="#b0b0b0", linewidth=0.9, alpha=0.65)

        for pair_index, ((left, right), zeta) in enumerate(zip(stage.pairings, stage.zetas)):
            color = colors[pair_index % len(colors)]
            x_mid = (previous_x + x) / 2
            ax.plot([previous_x + 0.35, x - 0.35], [-left, -left], color=color, linewidth=2.2)
            ax.plot([previous_x + 0.35, x - 0.35], [-right, -right], color=color, linewidth=2.2)
            ax.plot([x_mid, x_mid], [-left, -right], color=color, linewidth=2.6, alpha=0.95)
            ax.text(
                x_mid,
                -((left + right) / 2),
                f"zeta={zeta}",
                ha="center",
                va="center",
                fontsize=8,
                family="monospace",
                bbox={
                    "boxstyle": "round,pad=0.18",
                    "facecolor": "#ffffff",
                    "edgecolor": color,
                    "linewidth": 1.0,
                },
            )

    ax.set_xlim(-1.1, x_positions[-1] + 1.1)
    ax.set_ylim(-len(trace.input_values) + 0.2, 1.8)
    fig.tight_layout()
    return fig


def plot_stage_pairing_map(
    length: int,
    block_size: int,
    *,
    title: str | None = None,
):
    """Plot which indices talk to each other in one butterfly stage."""
    if title is None:
        title = f"Stage Pairing Map (n={length}, block={block_size})"

    pairs = stage_pairings(length, block_size)
    fig, ax = plt.subplots(figsize=(10, max(4.2, length * 0.55)))
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.axis("off")

    for index in range(length):
        ax.text(
            0,
            -index,
            f"{index}",
            ha="center",
            va="center",
            fontsize=10,
            family="monospace",
            bbox={"boxstyle": "round,pad=0.25", "facecolor": "#edf6f9", "edgecolor": "#264653"},
        )

    colors = ["#264653", "#2a9d8f", "#e76f51", "#8d99ae", "#c1121f", "#3a86ff"]
    for pair_index, (left, right) in enumerate(pairs):
        color = colors[pair_index % len(colors)]
        ax.plot([0.6, 4.2], [-left, -right], color=color, linewidth=2.4)
        ax.text(
            5.4,
            -((left + right) / 2),
            f"{left} <-> {right}",
            ha="center",
            va="center",
            fontsize=9,
            family="monospace",
            bbox={"boxstyle": "round,pad=0.22", "facecolor": "#ffffff", "edgecolor": color},
        )

    ax.text(0, 1.0, "indices", ha="center", va="center", fontsize=11, fontweight="bold")
    ax.text(5.4, 1.0, "pairs", ha="center", va="center", fontsize=11, fontweight="bold")
    ax.set_xlim(-1.0, 6.8)
    ax.set_ylim(-length + 0.2, 1.8)
    fig.tight_layout()
    return fig


def plot_stage_schedule(length: int, title: str | None = None):
    """Plot the full stage schedule for a power-of-two transform length."""
    if length <= 0 or length & (length - 1):
        raise ValueError("plot_stage_schedule requires a power-of-two length")
    if title is None:
        title = f"Butterfly Stage Schedule For n={length}"

    stages = []
    block_size = 2
    stage_index = 1
    while block_size <= length:
        stages.append(
            {
                "stage": stage_index,
                "block_size": block_size,
                "pair_distance": block_size // 2,
                "pair_count": len(stage_pairings(length, block_size)),
            }
        )
        block_size *= 2
        stage_index += 1

    fig, ax = plt.subplots(figsize=(11, max(4.5, len(stages) * 0.95)))
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.axis("off")

    headers = ["stage", "block", "distance", "pairs", "what happens"]
    x_positions = [0, 2.0, 4.0, 6.0, 9.2]
    for x, header in zip(x_positions, headers):
        ax.text(x, 1.0, header, ha="center", va="center", fontsize=11, fontweight="bold")

    for row_index, row in enumerate(stages):
        y = -row_index
        explanation = f"indices {row['pair_distance']} apart talk inside blocks of {row['block_size']}"
        values = [
            str(row["stage"]),
            str(row["block_size"]),
            str(row["pair_distance"]),
            str(row["pair_count"]),
            explanation,
        ]
        for x, value in zip(x_positions, values):
            ax.text(
                x,
                y,
                value,
                ha="center",
                va="center",
                fontsize=10,
                family="monospace",
                bbox={
                    "boxstyle": "round,pad=0.24",
                    "facecolor": "#edf6f9" if x < 8 else "#ffffff",
                    "edgecolor": "#264653",
                    "linewidth": 1.0,
                },
            )

    ax.set_xlim(-1.0, 12.3)
    ax.set_ylim(-len(stages) + 0.2, 1.7)
    fig.tight_layout()
    return fig


def plot_stage(stage: TransformStage, title: str | None = None):
    """Plot one explicit butterfly stage with input and output rows."""
    if title is None:
        title = f"{stage.algorithm.upper()} Stage {stage.stage_index}"

    fig, ax = plt.subplots(figsize=(max(8, len(stage.input_values) * 1.35), 5.8))
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.axis("off")

    input_y = 2.6
    output_y = 0.5
    _draw_value_row(ax, stage.input_values, input_y, "i")
    _draw_value_row(ax, stage.output_values, output_y, "o")

    colors = ["#264653", "#2a9d8f", "#e76f51", "#8d99ae", "#c1121f", "#3a86ff"]
    for pair_index, ((left, right), zeta) in enumerate(zip(stage.pairings, stage.zetas)):
        color = colors[pair_index % len(colors)]
        center_x = (left + right) / 2
        ax.plot([left, right], [input_y - 0.45, input_y - 0.45], color=color, linewidth=2.5)
        ax.plot([left, left], [input_y - 0.45, output_y + 0.55], color=color, linewidth=1.5, alpha=0.85)
        ax.plot([right, right], [input_y - 0.45, output_y + 0.55], color=color, linewidth=1.5, alpha=0.85)
        ax.text(
            center_x,
            1.55,
            f"pair {left}-{right}\nzeta={zeta}",
            ha="center",
            va="center",
            fontsize=10,
            family="monospace",
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "#ffffff",
                "edgecolor": color,
                "linewidth": 1.4,
            },
        )

    ax.text(
        len(stage.input_values) / 2 - 0.5,
        -0.05,
        stage.note,
        ha="center",
        va="center",
        fontsize=10,
        color="#333333",
    )
    ax.set_xlim(-0.8, len(stage.input_values) - 0.2)
    ax.set_ylim(-0.5, 3.3)
    fig.tight_layout()
    return fig


def plot_transform_pipeline(
    left: Sequence[int],
    right: Sequence[int],
    *,
    modulus: int,
    psi: int,
    title: str = "Transform-Domain Multiply Pipeline",
):
    """Plot the end-to-end direct NTT_psi multiply pipeline."""
    left_hat = forward_ntt_psi(left, modulus, psi)
    right_hat = forward_ntt_psi(right, modulus, psi)
    product_hat = pointwise_multiply(left_hat, right_hat, modulus)
    recovered = inverse_ntt_psi(product_hat, modulus, psi)

    lanes = [
        ("left", list(left)),
        ("right", list(right)),
        ("left_hat", left_hat),
        ("right_hat", right_hat),
        ("pointwise", product_hat),
        ("inverse", recovered),
    ]

    fig, ax = plt.subplots(figsize=(max(10, len(lanes) * 2.15), max(4.6, len(left) * 0.85)))
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.axis("off")

    for lane_index, (label, values) in enumerate(lanes):
        x = lane_index * 2.2
        for row_index, value in enumerate(values):
            ax.text(
                x,
                -row_index,
                str(value),
                ha="center",
                va="center",
                fontsize=10,
                family="monospace",
                bbox={
                    "boxstyle": "round,pad=0.24",
                    "facecolor": _value_colors([value])[0],
                    "edgecolor": "#222222",
                    "linewidth": 1.0,
                },
            )
        ax.text(x, 1.1, label, ha="center", va="center", fontsize=10, fontweight="bold")
        if lane_index < len(lanes) - 1:
            ax.annotate(
                "",
                xy=(x + 1.5, -len(values) / 2 + 0.4),
                xytext=(x + 0.6, -len(values) / 2 + 0.4),
                arrowprops={"arrowstyle": "->", "color": "#6c757d", "linewidth": 1.8},
            )

    ax.text(4.4, 1.6, "NTT_psi", ha="center", va="center", fontsize=10, family="monospace")
    ax.text(8.8, 1.6, "slotwise *", ha="center", va="center", fontsize=10, family="monospace")
    ax.text(11.0, 1.6, "INTT_psi", ha="center", va="center", fontsize=10, family="monospace")
    ax.set_xlim(-1.0, (len(lanes) - 1) * 2.2 + 1.1)
    ax.set_ylim(-len(left) + 0.2, 2.0)
    fig.tight_layout()
    return fig


def plot_base_multiply_pair_diagram(
    left: Sequence[int],
    right: Sequence[int],
    *,
    zeta: int,
    modulus: int,
    title: str = "Base Multiplication On A Degree-1 Pair",
):
    """Plot the two-term base multiplication block used in Kyber-style explanations."""
    if len(left) != 2 or len(right) != 2:
        raise ValueError("plot_base_multiply_pair_diagram expects two 2-entry vectors")

    result = base_multiply_pair(left, right, zeta, modulus)
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.axis("off")

    left_x = 0
    right_x = 2.8
    out_x = 6.8
    ys = [0.9, -0.7]

    for x, label, values, facecolor in [
        (left_x, "left", left, "#edf6f9"),
        (right_x, "right", right, "#fff3b0"),
        (out_x, "out", result, "#d8f3dc"),
    ]:
        ax.text(x, 1.8, label, ha="center", va="center", fontsize=12, fontweight="bold")
        for index, (y, value) in enumerate(zip(ys, values)):
            ax.text(
                x,
                y,
                f"{label}[{index}] = {value}",
                ha="center",
                va="center",
                fontsize=10,
                family="monospace",
                bbox={
                    "boxstyle": "round,pad=0.3",
                    "facecolor": facecolor,
                    "edgecolor": "#222222",
                    "linewidth": 1.0,
                },
            )

    ax.annotate("", xy=(left_x + 0.9, 0.1), xytext=(out_x - 1.0, 0.9), arrowprops={"arrowstyle": "->", "linewidth": 2.0, "color": "#355070"})
    ax.annotate("", xy=(left_x + 0.9, -0.7), xytext=(out_x - 1.0, -0.7), arrowprops={"arrowstyle": "->", "linewidth": 2.0, "color": "#355070"})
    ax.annotate("", xy=(right_x + 0.9, 0.1), xytext=(out_x - 1.0, 0.9), arrowprops={"arrowstyle": "->", "linewidth": 2.0, "color": "#6d597a"})
    ax.annotate("", xy=(right_x + 0.9, -0.7), xytext=(out_x - 1.0, -0.7), arrowprops={"arrowstyle": "->", "linewidth": 2.0, "color": "#6d597a"})

    ax.text(
        4.8,
        1.05,
        f"c0 = a0*b0 + zeta*a1*b1 mod {modulus}\n= {result[0]}",
        ha="center",
        va="center",
        fontsize=10,
        family="monospace",
        bbox={"boxstyle": "round,pad=0.32", "facecolor": "#ffffff", "edgecolor": "#355070"},
    )
    ax.text(
        4.8,
        -1.0,
        f"c1 = a0*b1 + a1*b0 mod {modulus}\n= {result[1]}",
        ha="center",
        va="center",
        fontsize=10,
        family="monospace",
        bbox={"boxstyle": "round,pad=0.32", "facecolor": "#ffffff", "edgecolor": "#6d597a"},
    )
    ax.text(4.8, 0.0, f"zeta = {zeta}", ha="center", va="center", fontsize=10, family="monospace")
    ax.set_xlim(-1.0, 8.2)
    ax.set_ylim(-2.0, 2.2)
    fig.tight_layout()
    return fig


def plot_root_order_comparison(samples: Sequence[tuple[int, int]], title: str = "Root Existence Check"):
    """Plot which moduli allow n-th and 2n-th root stories."""
    fig, ax = plt.subplots(figsize=(10, max(4.5, len(samples) * 0.75)))
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.axis("off")

    headers = ["n", "q", "n | q-1", "2n | q-1"]
    x_positions = [0, 2, 4.2, 6.8]
    for x, header in zip(x_positions, headers):
        ax.text(x, 1.2, header, ha="center", va="center", fontsize=11, fontweight="bold")

    for row_index, (n, q) in enumerate(samples):
        y = -row_index
        statuses = [str(n), str(q), "yes" if (q - 1) % n == 0 else "no", "yes" if (q - 1) % (2 * n) == 0 else "no"]
        for x, value in zip(x_positions, statuses):
            facecolor = "#d8f3dc" if value == "yes" else "#f5cac3" if value == "no" else "#edf6f9"
            ax.text(
                x,
                y,
                value,
                ha="center",
                va="center",
                fontsize=10,
                family="monospace",
                bbox={"boxstyle": "round,pad=0.25", "facecolor": facecolor, "edgecolor": "#222222"},
            )

    ax.set_xlim(-1.0, 8.0)
    ax.set_ylim(-len(samples) + 0.2, 1.8)
    fig.tight_layout()
    return fig


def plot_trace_overview(trace: TransformTrace, title: str | None = None):
    """Plot every stage output as a column of values."""
    if title is None:
        title = f"{trace.algorithm.upper()} Trace Overview"

    columns = [trace.input_values] + [stage.output_values for stage in trace.stages]
    fig, ax = plt.subplots(figsize=(max(9, len(columns) * 2.0), max(4.5, len(trace.input_values) * 0.7)))
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.axis("off")

    for column_index, values in enumerate(columns):
        x = column_index * 2.0
        for row_index, value in enumerate(values):
            ax.text(
                x,
                -row_index,
                str(value),
                ha="center",
                va="center",
                fontsize=10,
                family="monospace",
                bbox={
                    "boxstyle": "round,pad=0.25",
                    "facecolor": _value_colors([value])[0],
                    "edgecolor": "#222222",
                    "linewidth": 1.0,
                },
            )
        if column_index == 0:
            label = "input"
        else:
            label = f"stage {column_index}"
        ax.text(x, 1, label, ha="center", va="center", fontsize=11, fontweight="bold")

    ax.set_xlim(-1.0, (len(columns) - 1) * 2.0 + 1.0)
    ax.set_ylim(-len(trace.input_values) + 0.2, 1.8)
    fig.tight_layout()
    return fig


def interactive_trace(trace: TransformTrace, title: str | None = None):
    """Return a slider-based stage explorer for a transform trace."""
    if title is None:
        title = f"{trace.algorithm.upper()} Stage Explorer"

    slider = widgets.IntSlider(
        value=1,
        min=1,
        max=max(1, len(trace.stages)),
        step=1,
        description="Stage",
        continuous_update=False,
    )
    output = widgets.Output()

    def render(stage_index: int) -> None:
        with output:
            clear_output(wait=True)
            stage = trace.stages[stage_index - 1]
            fig = plot_stage(stage, title=f"{title} | Stage {stage_index}")
            display(fig)
            plt.close(fig)
            rows = []
            for pair, zeta in zip(stage.pairings, stage.zetas):
                left, right = pair
                rows.append(
                    f"pair {pair}: inputs=({stage.input_values[left]}, {stage.input_values[right]}) "
                    f"-> outputs=({stage.output_values[left]}, {stage.output_values[right]}) | zeta={zeta}"
                )
            print("\n".join(rows))

    slider.observe(lambda change: render(change["new"]), names="value")
    render(slider.value)
    widget = widgets.VBox([widgets.HTML(f"<h4>{title}</h4>"), slider, output])
    return widget


def show_trace(trace: TransformTrace, title: str | None = None):
    """Display the interactive trace widget immediately."""
    widget = interactive_trace(trace, title=title)
    display(widget)
    return widget
