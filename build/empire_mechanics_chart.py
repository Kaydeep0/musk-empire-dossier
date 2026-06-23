#!/usr/bin/env python3
"""EMPIRE MECHANICS — the recurring-actor role matrix.
Renders charts/EMPIRE_actors.png : who plays which role (owner/creditor/board/pay-setter/operator)
across Tesla, SolarCity, SpaceX, X/xAI. The throughline: the same names recur on multiple sides.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = os.path.dirname(__file__)

actors = ["Elon Musk", "Antonio Gracias\n(Valor)", "JB Straubel", "Kimbal Musk", "Lyndon & Peter\nRive"]
roles = ["Owner /\nholder", "Creditor /\nlessor", "Board\nseat", "Comp /\npay-setter", "Operator /\nCEO", "Counter-\nparty"]

# cell -> short entity tag(s) showing where the actor plays that role. "" = none.
M = {
 ("Elon Musk","Owner /\nholder"): "TSLA\nSPCX\nSCTY\nX/xAI",
 ("Elon Musk","Creditor /\nlessor"): "SCTY\n$65M bonds",
 ("Elon Musk","Board\nseat"): "TSLA\nSPCX\n(SCTY chmn)",
 ("Elon Musk","Comp /\npay-setter"): "recipient\n$120B+$1T",
 ("Elon Musk","Operator /\nCEO"): "TSLA\nSPCX\nX",
 ("Elon Musk","Counter-\nparty"): "security co\naircraft",
 ("Antonio Gracias\n(Valor)","Owner /\nholder"): "SPCX #2\n~7.3%",
 ("Antonio Gracias\n(Valor)","Creditor /\nlessor"): "SPCX\n~$20B leases",
 ("Antonio Gracias\n(Valor)","Board\nseat"): "TSLA SPCX\n(SCTY recuse)",
 ("Antonio Gracias\n(Valor)","Comp /\npay-setter"): "SPCX comp\ncommittee",
 ("JB Straubel","Board\nseat"): "TSLA\ndirector",
 ("JB Straubel","Operator /\nCEO"): "Redwood\nCEO",
 ("JB Straubel","Counter-\nparty"): "Redwood\n$30.3M scrap",
 ("Kimbal Musk","Owner /\nholder"): "TSLA\nholder",
 ("Kimbal Musk","Board\nseat"): "TSLA SPCX\ndirector",
 ("Kimbal Musk","Operator /\nCEO"): "Nova Sky\nStories CEO",
 ("Kimbal Musk","Counter-\nparty"): "Nova Sky\n$0.3M",
 ("Lyndon & Peter\nRive","Owner /\nholder"): "SCTY\nfounders",
 ("Lyndon & Peter\nRive","Operator /\nCEO"): "SCTY\nCEO/CTO",
}

nr, nc = len(actors), len(roles)
fig, ax = plt.subplots(figsize=(13, 6.4))
for i, a in enumerate(actors):
    y = nr - 1 - i
    for j, r in enumerate(roles):
        txt = M.get((a, r), "")
        filled = bool(txt)
        ax.add_patch(Rectangle((j, y), 1, 1, facecolor=("#7a2230" if filled else "#f3f3f3"),
                               edgecolor="white", lw=2, alpha=(0.88 if filled else 1)))
        if filled:
            ax.text(j + 0.5, y + 0.5, txt, ha="center", va="center", fontsize=7.4,
                    color="white", fontweight="bold")
# role count per actor (how many hats)
for i, a in enumerate(actors):
    y = nr - 1 - i
    hats = sum(1 for r in roles if M.get((a, r)))
    ax.text(nc + 0.15, y + 0.5, f"{hats} hats", ha="left", va="center",
            fontsize=9, color="#7a2230", fontweight="bold")

ax.set_xlim(0, nc + 1.1); ax.set_ylim(0, nr)
ax.set_xticks([j + 0.5 for j in range(nc)]); ax.set_xticklabels(roles, fontsize=9)
ax.set_yticks([nr - 1 - i + 0.5 for i in range(nr)]); ax.set_yticklabels(actors, fontsize=10)
ax.xaxis.tick_top(); ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
ax.set_title("EMPIRE MECHANICS \u00b7 the same names recur as owner, creditor, board & pay-setter",
             fontsize=13, fontweight="bold", pad=34)
fig.text(0.5, 0.015,
         "TSLA=Tesla \u00b7 SPCX=SpaceX \u00b7 SCTY=SolarCity \u00b7 X/xAI. Sources: Tesla 2025 DEF 14A (b), "
         "2016 merger proxy (b), SPCX 424(b)(4) dossier (b). Educational only \u2014 not investment advice.",
         ha="center", fontsize=7.6, color="#666")
fig.tight_layout(rect=[0, 0.035, 1, 1])
out = os.path.join(HERE, "..", "charts", "EMPIRE_actors.png")
fig.savefig(out, dpi=150)
print("wrote", out)
