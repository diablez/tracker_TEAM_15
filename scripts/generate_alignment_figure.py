#!/usr/bin/env python3
"""Generate the alignment comparison SVG from preserved Construct logs."""

import argparse
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BEFORE = ROOT / 'docs/evidence/2026-10-21/team15_alignment_readonly.log'
DEFAULT_AFTER = ROOT / 'docs/evidence/2026-10-21/team15_alignment_after.log'
DEFAULT_OUTPUT = ROOT / 'docs/figures/alignment_before_after.svg'


def load_metrics(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    return {
        robot: {
            'median_cm': data[robot]['dist_median_p90'][0] * 100.0,
            'p90_cm': data[robot]['dist_median_p90'][1] * 100.0,
            'within_10_pct': data[robot]['within_10cm'] * 100.0,
        }
        for robot in ('0', '1')
    }


def render(before, after):
    width, height = 900, 470
    left, top, plot_width, plot_height = 92, 88, 750, 260
    maximum = 150.0
    groups = [
        ('Red median', before['0']['median_cm'], after['0']['median_cm']),
        ('Red 90th', before['0']['p90_cm'], after['0']['p90_cm']),
        ('Green median', before['1']['median_cm'], after['1']['median_cm']),
        ('Green 90th', before['1']['p90_cm'], after['1']['p90_cm']),
    ]
    bar_width, gap = 42, 58
    start_x = 135
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<style>text{font-family:system-ui,-apple-system,sans-serif;fill:#17202a}.title{font-size:22px;font-weight:700}.sub{font-size:13px;fill:#566573}.axis{font-size:12px}.label{font-size:12px;font-weight:600}.value{font-size:11px}</style>',
        '<text class="title" x="450" y="32" text-anchor="middle">Laser-to-map alignment before and after AMCL correction</text>',
        '<text class="sub" x="450" y="55" text-anchor="middle">Latest scan after each 20-scan acquisition; nearest occupied-cell error, 21 Oct 2026</text>',
    ]
    for tick in (0, 50, 100, 150):
        y = top + plot_height - tick / maximum * plot_height
        parts.extend([
            f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_width}" y2="{y:.1f}" stroke="#d5d8dc"/>',
            f'<text class="axis" x="{left - 10}" y="{y + 4:.1f}" text-anchor="end">{tick}</text>',
        ])
    parts.append(f'<text class="axis" transform="translate(22 {top + plot_height / 2}) rotate(-90)" text-anchor="middle">Error (cm)</text>')
    for index, (label, before_value, after_value) in enumerate(groups):
        x = start_x + index * (2 * bar_width + gap)
        for offset, value, color, state in (
            (0, before_value, '#c0392b', 'Before'),
            (bar_width, after_value, '#1f8a70', 'After'),
        ):
            bar_height = value / maximum * plot_height
            y = top + plot_height - bar_height
            parts.extend([
                f'<rect x="{x + offset}" y="{y:.1f}" width="{bar_width - 4}" height="{bar_height:.1f}" rx="2" fill="{color}"/>',
                f'<text class="value" x="{x + offset + (bar_width - 4) / 2:.1f}" y="{max(y - 6, 76):.1f}" text-anchor="middle">{value:.1f}</text>',
                f'<title>{html.escape(label)} {state}: {value:.3f} cm</title>',
            ])
        parts.append(f'<text class="label" x="{x + bar_width - 2}" y="{top + plot_height + 24}" text-anchor="middle">{html.escape(label)}</text>')
    parts.extend([
        '<rect x="300" y="405" width="16" height="16" fill="#c0392b"/><text class="axis" x="324" y="418">Before correction</text>',
        '<rect x="480" y="405" width="16" height="16" fill="#1f8a70"/><text class="axis" x="504" y="418">After correction</text>',
        (f'<text class="sub" x="450" y="450" text-anchor="middle">'
         f'Within 10 cm: Red {before["0"]["within_10_pct"]:.1f}% → {after["0"]["within_10_pct"]:.1f}%; '
         f'Green {before["1"]["within_10_pct"]:.1f}% → {after["1"]["within_10_pct"]:.1f}%'
         '</text>'),
        '</svg>',
    ])
    return '\n'.join(parts) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, default=DEFAULT_BEFORE)
    parser.add_argument('--after', type=Path, default=DEFAULT_AFTER)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        render(load_metrics(args.before), load_metrics(args.after)),
        encoding='utf-8',
    )
    print(args.output)


if __name__ == '__main__':
    main()
