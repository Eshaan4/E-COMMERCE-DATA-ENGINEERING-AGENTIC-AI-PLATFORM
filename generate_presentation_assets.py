"""
generate_presentation_assets.py – Generates professional high-resolution visual diagrams
to embed into the PowerPoint presentation slides.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Set dark theme for figures to match presentation aesthetic
plt.style.use('dark_background')

def generate_medallion_diagram(filename="medallion_diagram.png"):
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
    fig.patch.set_facecolor('#0F172A')
    ax.set_facecolor('#0F172A')
    ax.axis('off')

    # Draw 4 main pipeline blocks
    blocks = [
        {"title": "RAW SOURCES\n(CSV, JSON, APIs)", "color": "#475569", "x": 0.5},
        {"title": "BRONZE LAYER\n(Raw Storage)", "color": "#D97706", "x": 3.0},
        {"title": "SILVER LAYER\n(Cleansed & SCD2)", "color": "#64748B", "x": 5.5},
        {"title": "GOLD LAYER\n(Star Schema & Marts)", "color": "#EAB308", "x": 8.0},
    ]

    for b in blocks:
        rect = patches.FancyBboxPatch((b["x"], 1.2), 1.8, 2.0, boxstyle="round,pad=0.1",
                                      ec="#CBD5E1", fc=b["color"], lw=1.5)
        ax.add_patch(rect)
        ax.text(b["x"] + 0.9, 2.2, b["title"], color="white", fontsize=10,
                fontweight="bold", ha="center", va="center")

    # Draw arrows
    arrow_props = dict(facecolor='#6366F1', edgecolor='#6366F1', width=2, headwidth=8)
    ax.annotate('', xy=(2.9, 2.2), xytext=(2.4, 2.2), arrowprops=arrow_props)
    ax.annotate('', xy=(5.4, 2.2), xytext=(4.9, 2.2), arrowprops=arrow_props)
    ax.annotate('', xy=(7.9, 2.2), xytext=(7.4, 2.2), arrowprops=arrow_props)

    plt.tight_layout()
    plt.savefig(filename, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Generated: {filename}")


def generate_agent_flow_diagram(filename="agent_flow_diagram.png"):
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
    fig.patch.set_facecolor('#0F172A')
    ax.set_facecolor('#0F172A')
    ax.axis('off')

    # User Input
    rect_user = patches.FancyBboxPatch((0.4, 1.8), 1.6, 1.2, boxstyle="round,pad=0.1", ec="#38BDF8", fc="#0284C7", lw=1.5)
    ax.add_patch(rect_user)
    ax.text(1.2, 2.4, "USER QUESTION\n'Why did profit drop?'", color="white", fontsize=8.5, fontweight="bold", ha="center", va="center")

    # Router
    rect_router = patches.FancyBboxPatch((2.6, 1.8), 1.6, 1.2, boxstyle="round,pad=0.1", ec="#818CF8", fc="#4F46E5", lw=1.5)
    ax.add_patch(rect_router)
    ax.text(3.4, 2.4, "AUTO ROUTER 🤖\nSelects Agents Chain", color="white", fontsize=8.5, fontweight="bold", ha="center", va="center")

    # Data Agent
    rect_data = patches.FancyBboxPatch((4.8, 2.8), 1.6, 1.0, boxstyle="round,pad=0.1", ec="#34D399", fc="#059669", lw=1.5)
    ax.add_patch(rect_data)
    ax.text(5.6, 3.3, "DATA AGENT 📊\nExecutes Read SQL", color="white", fontsize=8, fontweight="bold", ha="center", va="center")

    # Insight Agent
    rect_ins = patches.FancyBboxPatch((4.8, 1.0), 1.6, 1.0, boxstyle="round,pad=0.1", ec="#FBBF24", fc="#D97706", lw=1.5)
    ax.add_patch(rect_ins)
    ax.text(5.6, 1.5, "INSIGHT AGENT 💡\nExplains Trends", color="white", fontsize=8, fontweight="bold", ha="center", va="center")

    # Action Agent
    rect_act = patches.FancyBboxPatch((7.0, 1.8), 1.6, 1.2, boxstyle="round,pad=0.1", ec="#F472B6", fc="#DB2777", lw=1.5)
    ax.add_patch(rect_act)
    ax.text(7.8, 2.4, "ACTION AGENT 🎯\nRecommends Solution", color="white", fontsize=8.5, fontweight="bold", ha="center", va="center")

    # Output
    rect_out = patches.FancyBboxPatch((9.2, 1.8), 1.5, 1.2, boxstyle="round,pad=0.1", ec="#A78BFA", fc="#7C3AED", lw=1.5)
    ax.add_patch(rect_out)
    ax.text(9.95, 2.4, "STREAMLIT UI\nChart + Action Card", color="white", fontsize=8.5, fontweight="bold", ha="center", va="center")

    # Arrows
    arrow = dict(facecolor='#94A3B8', edgecolor='#94A3B8', width=1.5, headwidth=6)
    ax.annotate('', xy=(2.5, 2.4), xytext=(2.1, 2.4), arrowprops=arrow)
    ax.annotate('', xy=(4.7, 3.3), xytext=(4.3, 2.6), arrowprops=arrow)
    ax.annotate('', xy=(4.7, 1.5), xytext=(4.3, 2.2), arrowprops=arrow)
    ax.annotate('', xy=(6.9, 2.4), xytext=(6.5, 2.4), arrowprops=arrow)
    ax.annotate('', xy=(9.1, 2.4), xytext=(8.7, 2.4), arrowprops=arrow)

    plt.tight_layout()
    plt.savefig(filename, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Generated: {filename}")


def generate_forecast_chart_image(filename="forecast_chart.png"):
    fig, ax = plt.subplots(figsize=(8, 4), dpi=300)
    fig.patch.set_facecolor('#1E293B')
    ax.set_facecolor('#1E293B')

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep (FC)", "Oct (FC)", "Nov (FC)"]
    hist_rev = [120, 135, 128, 142, 155, 150, 168, 175, None, None, None]
    fc_rev = [None, None, None, None, None, None, None, 175, 184, 192, 201]
    trend = [120, 128, 136, 144, 152, 160, 168, 176, 184, 192, 200]

    ax.plot(months[:8], hist_rev[:8], marker='o', color='#6366F1', linewidth=2.5, label='Historical Revenue')
    ax.plot(months[7:], fc_rev[7:], marker='D', color='#F59E0B', linewidth=2.5, linestyle='--', label='Forecast (Linear Extrapolation)')
    ax.plot(months, trend, color='#EF4444', linewidth=1.5, linestyle=':', label='Linear Trend Slope')

    ax.set_title("Revenue Forecast Analysis (Historical vs Extrapolated)", color='white', fontsize=11, fontweight='bold', pad=10)
    ax.set_ylabel("Revenue ($K)", color='#94A3B8', fontsize=9)
    ax.tick_params(colors='#94A3B8', labelsize=8)
    ax.grid(True, color='#334155', linestyle='--', alpha=0.5)
    ax.legend(facecolor='#0F172A', edgecolor='#475569', labelcolor='white', fontsize=8)

    plt.tight_layout()
    plt.savefig(filename, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Generated: {filename}")

if __name__ == "__main__":
    generate_medallion_diagram()
    generate_agent_flow_diagram()
    generate_forecast_chart_image()
