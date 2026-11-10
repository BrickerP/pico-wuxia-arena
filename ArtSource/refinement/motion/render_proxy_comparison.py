"""Plot the verified source-derived proxy centres in character-root YZ space."""

import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Polygon


HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "proxy_alignment_profiles.json").read_text())
base = next(actor for actor in data["actors"] if actor["actor"] == "base")
legacy = base["calibration"]["legacy_points_metres"]
slash = next(key for key in base["keyposes"] if key["source_seconds"] == 2.167)
current = {role: value["root_position_metres"] for role, value in slash["proxies"].items()}
OLD, NEW = "#d67426", "#137bb5"


def yz(point):
    return point[2], point[1]


def capsule(bottom, top, radius):
    a, b = yz(bottom), yz(top)
    heading = math.atan2(b[1] - a[1], b[0] - a[0])
    points = []
    for centre, start in ((b, heading - math.pi / 2), (a, heading + math.pi / 2)):
        for index in range(33):
            angle = start + math.pi * index / 32
            points.append((centre[0] + radius * math.cos(angle), centre[1] + radius * math.sin(angle)))
    return points


def draw(ax, points, colour, dashed=False):
    style = "--" if dashed else "-"
    ax.add_patch(Polygon(capsule(points["body_bottom"], points["body_top"], .24),
                         closed=True, fill=False, edgecolor=colour, linewidth=2.6, linestyle=style))
    ax.add_patch(Circle(yz(points["head"]), .16, fill=False,
                        edgecolor=colour, linewidth=2.6, linestyle=style))
    a, b = yz(points["body_bottom"]), yz(points["body_top"])
    ax.plot((a[0], b[0]), (a[1], b[1]), color=colour, linestyle=style, linewidth=1.4)


fig, axes = plt.subplots(1, 2, figsize=(12, 7.3), sharex=True, sharey=True)
fig.patch.set_facecolor("#f8fafc")
for ax, points, title in zip(axes, (legacy, current), ("idle @ 1.000 s", "slash @ 2.167 s")):
    ax.set_facecolor("white")
    ax.set_title(title, loc="left", fontsize=16, fontweight="bold", pad=14)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-.65, 1.05)
    ax.set_ylim(0, 2.05)
    ax.set_xticks([-.5, 0, .5, 1.0])
    ax.set_yticks([0, .5, 1.0, 1.5, 2.0])
    ax.grid(color="#dfe5ec", linewidth=.8)
    ax.axvline(0, color="#95a4b8", linewidth=1)
    ax.set_xlabel("Z / m  (+Z = actor front)", fontsize=11)
    ax.tick_params(labelsize=10)
    for spine in ax.spines.values():
        spine.set_color("#c7d2df")
    draw(ax, legacy, OLD, True)
    draw(ax, points, NEW)
    for role, label in (("head", "H"), ("body_top", "T"), ("body_bottom", "B")):
        point = yz(points[role])
        ax.scatter(*point, s=27, color=NEW, zorder=6)
        ax.annotate(label, point, xytext=(7, 6), textcoords="offset points", color=NEW,
                    fontsize=11, fontweight="bold")
axes[0].set_ylabel("Y / m", fontsize=11)
axes[0].text(-.53, 1.92, "Coincident at the calibration pose", fontsize=10, color="#475569")
axes[1].annotate("Head moves down and forward", xy=yz(current["head"]), xytext=(-.55, 1.92),
                 arrowprops={"arrowstyle": "->", "color": NEW, "lw": 1.1}, fontsize=10, color=NEW)
fig.suptitle("Base actor — source-derived contact proxy alignment", x=.07, ha="left", y=.985,
             fontsize=19, fontweight="bold", color="#0f172a")
fig.legend([Line2D([0], [0], color=OLD, linestyle="--", lw=2.6),
            Line2D([0], [0], color=NEW, lw=2.6)],
           ["Legacy fixed proxy", "Calibrated bone-following centres"], loc="upper center",
           bbox_to_anchor=(.5, .93), ncol=2, frameon=False, fontsize=11)
fig.text(.07, .095, "H = Head   T = body top / Spine02   B = body bottom / Hip.   Radii unchanged: head 0.16 m, body 0.24 m.",
         fontsize=9.5, color="#334155")
fig.text(.07, .062, "Offline source bone-derived anchors. YZ projection omits X motion. Not a game screenshot or a skin-surface outline.",
         fontsize=9.5, color="#334155")
fig.text(.07, .029, "Source base.glb SHA-256 a0122103a6bc…   |   glTF / Blender keypose cross-check < 0.9 micrometres.",
         fontsize=9, color="#64748b")
fig.subplots_adjust(left=.075, right=.965, top=.84, bottom=.18, wspace=.12)
for suffix in ("svg", "png"):
    output = HERE / ("proxy_alignment_sideview." + suffix)
    fig.savefig(output, dpi=160, facecolor=fig.get_facecolor())
    if suffix == "svg":
        output.write_text("\n".join(line.rstrip() for line in output.read_text().splitlines()) + "\n")
    print(output)
