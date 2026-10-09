from __future__ import annotations

from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from openpyxl.styles import Alignment, Font, PatternFill

from core.metrics import calculate_metrics
from core.thermodynamics import ROUTE_META, SPECIES, run_temperature_sweep, solve_equilibrium

APP_DIR = Path(__file__).parent

st.set_page_config(
    page_title="H₂ Reform Lab · Methane Reforming PoC",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Diseño visual
# -----------------------------------------------------------------------------
st.markdown(
    """
<style>
:root {
  --ink: #eaf2ff; --muted: #91a4bd; --panel: #0d1a2a;
  --panel-2: #111f31; --line: rgba(145, 164, 189, .16);
  --green: #2ee6a6; --blue: #56b4ff; --orange: #ffb86b;
}
.stApp { background: radial-gradient(circle at 82% 4%, #142943 0, #08111e 34%, #060d18 100%); }
.block-container { max-width: 1480px; padding-top: 1.4rem; padding-bottom: 4rem; }
[data-testid="stSidebar"] { background: #07111f; border-right: 1px solid var(--line); }
[data-testid="stSidebar"] .block-container { padding-top: 1.25rem; }
[data-testid="stSidebar"] hr { border-color: var(--line); }
[data-baseweb="tab-list"] { gap: 1.6rem; border-bottom: 1px solid var(--line); }
[data-baseweb="tab"] { height: 3.2rem; padding: 0 .15rem; color: var(--muted); }
[data-baseweb="tab"][aria-selected="true"] { color: var(--ink); }
[data-testid="stMetric"] { background: var(--panel); border: 1px solid var(--line); border-radius: 15px; padding: 1rem; }
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
.stDownloadButton button, .stButton button { border-radius: 10px; border: 1px solid rgba(46,230,166,.35); }
.stDownloadButton button:hover, .stButton button:hover { border-color: #2ee6a6; color: #2ee6a6; }
.hero {
  position: relative; overflow: hidden; border: 1px solid var(--line); border-radius: 22px;
  padding: 28px 30px 24px; margin: 2px 0 20px;
  background: linear-gradient(120deg, rgba(17,31,49,.98), rgba(9,22,37,.94));
  box-shadow: 0 18px 45px rgba(0,0,0,.18);
}
.hero:after { content:""; position:absolute; width:320px; height:320px; right:-115px; top:-165px; border-radius:50%; background:var(--accent); opacity:.12; filter:blur(2px); }
.eyebrow { color: var(--accent); font-size:.73rem; font-weight:750; letter-spacing:.14em; text-transform:uppercase; margin-bottom:.5rem; }
.hero h1 { color:var(--ink); font-size:2.05rem; letter-spacing:-.035em; line-height:1.1; margin:.15rem 0 .55rem; }
.hero p { color:var(--muted); font-size:.98rem; margin:0; max-width:850px; line-height:1.55; }
.chip-row { display:flex; flex-wrap:wrap; gap:.45rem; margin-top:1.15rem; }
.chip { color:#b9cae0; background:rgba(255,255,255,.035); border:1px solid var(--line); border-radius:999px; padding:.28rem .62rem; font-size:.72rem; }
.section-kicker { color:var(--muted); text-transform:uppercase; font-weight:700; letter-spacing:.1em; font-size:.68rem; margin:1.35rem 0 .25rem; }
.section-title { color:var(--ink); font-size:1.18rem; font-weight:700; letter-spacing:-.015em; margin:0 0 1rem; }
.kpi { min-height:143px; background:linear-gradient(145deg, rgba(17,31,49,.98), rgba(10,24,39,.98)); border:1px solid var(--line); border-radius:16px; padding:1.05rem 1.08rem; }
.kpi-top { display:flex; justify-content:space-between; align-items:center; gap:.5rem; }
.kpi-label { color:var(--muted); font-size:.73rem; line-height:1.2; text-transform:uppercase; letter-spacing:.055em; }
.kpi-dot { width:7px; height:7px; border-radius:50%; background:var(--accent); box-shadow:0 0 12px var(--accent); }
.kpi-value { color:var(--ink); font-weight:760; font-size:1.75rem; letter-spacing:-.035em; margin:.72rem 0 .22rem; }
.kpi-note { color:#71859f; font-size:.7rem; line-height:1.35; }
.surface { background:rgba(13,26,42,.82); border:1px solid var(--line); border-radius:16px; padding:1rem 1.05rem; }
.route-card { display:flex; align-items:center; justify-content:space-between; gap:1rem; background:linear-gradient(90deg, rgba(46,230,166,.08), rgba(86,180,255,.03)); border:1px solid var(--line); border-left:3px solid var(--accent); border-radius:14px; padding:.9rem 1.05rem; margin:.4rem 0 1.1rem; }
.route-name { color:var(--ink); font-weight:720; font-size:.93rem; }
.route-desc { color:var(--muted); font-size:.75rem; margin-top:.18rem; }
.reaction { white-space:nowrap; color:var(--accent); font-family:ui-monospace, SFMono-Regular, Menlo, monospace; font-size:.88rem; }
.process { display:grid; grid-template-columns:1fr auto 1fr auto 1fr auto 1fr; align-items:center; gap:.55rem; margin:.25rem 0 1rem; }
.process-node { min-height:82px; background:rgba(13,26,42,.78); border:1px solid var(--line); border-radius:13px; padding:.75rem; }
.process-node b { color:var(--ink); font-size:.79rem; display:block; margin-bottom:.25rem; }
.process-node span { color:var(--muted); font-size:.67rem; line-height:1.3; display:block; }
.process-arrow { color:var(--accent); font-size:1.05rem; }
.insight { border:1px solid rgba(86,180,255,.22); background:rgba(86,180,255,.055); border-radius:14px; padding:.9rem 1rem; color:#b8cbe2; font-size:.79rem; line-height:1.55; }
.insight b { color:#dceaff; }
.status-ok { color:#2ee6a6; font-weight:700; }
.status-warn { color:#ffb86b; font-weight:700; }
.phase { height:100%; background:rgba(13,26,42,.84); border:1px solid var(--line); border-radius:15px; padding:1rem; }
.phase-num { color:var(--accent); font-size:.68rem; font-weight:800; letter-spacing:.12em; }
.phase h4 { color:var(--ink); margin:.35rem 0 .45rem; font-size:.94rem; }
.phase p { color:var(--muted); font-size:.71rem; line-height:1.45; margin:0; }
.arch { display:flex; align-items:stretch; gap:.45rem; flex-wrap:wrap; }
.arch-box { flex:1; min-width:150px; background:rgba(13,26,42,.85); border:1px solid var(--line); border-radius:13px; padding:.85rem; }
.arch-box b { color:var(--ink); font-size:.78rem; display:block; }
.arch-box span { color:var(--muted); font-size:.68rem; line-height:1.35; display:block; margin-top:.3rem; }
.arch-arrow { align-self:center; color:var(--accent); }
.sidebar-brand { padding:.15rem 0 .75rem; }
.sidebar-brand b { color:var(--ink); font-size:1rem; letter-spacing:-.02em; }
.sidebar-brand span { color:var(--green); }
.sidebar-brand small { display:block; color:var(--muted); font-size:.65rem; margin-top:.15rem; letter-spacing:.06em; text-transform:uppercase; }
.sidebar-status { display:flex; align-items:center; gap:.45rem; color:var(--muted); font-size:.68rem; padding:.55rem .65rem; background:rgba(46,230,166,.04); border:1px solid rgba(46,230,166,.15); border-radius:10px; }
.sidebar-status i { width:7px; height:7px; border-radius:50%; background:var(--green); display:block; box-shadow:0 0 9px var(--green); }
.footer-note { color:#647991; font-size:.67rem; line-height:1.5; border-top:1px solid var(--line); margin-top:2rem; padding-top:1rem; }
@media (max-width: 900px) { .process { grid-template-columns:1fr; } .process-arrow { transform:rotate(90deg); text-align:center; } .route-card { align-items:flex-start; flex-direction:column; } .reaction { white-space:normal; } }
</style>
""",
    unsafe_allow_html=True,
)

PLOT = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"family": "Inter, system-ui, sans-serif", "color": "#91a4bd", "size": 11},
    "title": {"font": {"color": "#eaf2ff", "size": 15}, "x": 0.02, "xanchor": "left"},
    "margin": {"l": 38, "r": 25, "t": 55, "b": 38},
    "hoverlabel": {"bgcolor": "#101f31", "bordercolor": "#263b54", "font": {"color": "#eaf2ff"}},
    "legend": {"orientation": "h", "y": 1.13, "x": 0.01, "font": {"size": 10}},
}
GRID = "rgba(145,164,189,.10)"


def style_figure(fig: go.Figure, height: int = 390) -> go.Figure:
    fig.update_layout(**PLOT, height=height)
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    return fig


def kpi_card(label: str, value: str, note: str, accent: str) -> None:
    st.markdown(
        f"""<div class="kpi" style="--accent:{accent}">
        <div class="kpi-top"><span class="kpi-label">{label}</span><span class="kpi-dot"></span></div>
        <div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>""",
        unsafe_allow_html=True,
    )


def section_header(kicker: str, title: str) -> None:
    st.markdown(
        f'<div class="section-kicker">{kicker}</div><div class="section-title">{title}</div>',
        unsafe_allow_html=True,
    )


def excel_package(
    sweep: pd.DataFrame,
    composition: pd.DataFrame,
    inputs: dict,
) -> bytes:
    output = BytesIO()
    assumptions = pd.DataFrame(
        {
            "Supuesto": [
                "Fase",
                "Modelo termodinámico",
                "Especies incluidas",
                "Estado del reactor",
                "Pérdida de presión",
                "Formación de coque",
                "Base de carbono",
                "Uso recomendado",
            ],
            "Valor": [
                "Gas ideal",
                "Minimización de Gibbs con datos Shomate NIST",
                ", ".join(SPECIES),
                "Isotérmico; equilibrio químico",
                "No incluida",
                "No incluida: se requiere C(s) y submodelo cinético",
                "CO + CO2 como CO2 potencial aguas abajo",
                "Screening / prueba de concepto; no diseño detallado",
            ],
        }
    )
    references = pd.read_csv(APP_DIR / "data" / "literature_matrix.csv")
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        sweep.to_excel(writer, sheet_name="Barrido_T", index=False)
        composition.to_excel(writer, sheet_name="Composicion", index=False)
        pd.DataFrame({"Parámetro": inputs.keys(), "Valor": inputs.values()}).to_excel(
            writer, sheet_name="Entradas", index=False
        )
        assumptions.to_excel(writer, sheet_name="Supuestos", index=False)
        references.to_excel(writer, sheet_name="Referencias", index=False)
        for sheet in writer.book.worksheets:
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            for cell in sheet[1]:
                cell.fill = PatternFill("solid", fgColor="16324F")
                cell.font = Font(color="FFFFFF", bold=True)
                cell.alignment = Alignment(vertical="center")
            for column in sheet.columns:
                width = min(55, max(12, max(len(str(c.value or "")) for c in column) + 2))
                sheet.column_dimensions[column[0].column_letter].width = width
    return output.getvalue()


def normalize_upload(frame: pd.DataFrame) -> pd.DataFrame:
    aliases = {
        "temperatura_c": "Temperatura_C",
        "temperatura (°c)": "Temperatura_C",
        "temperature_c": "Temperatura_C",
        "presion_bar": "Presion_bar",
        "presión (bar)": "Presion_bar",
        "pressure_bar": "Presion_bar",
        "ratio": "Ratio",
        "relación de alimentación": "Ratio",
        "ruta": "Ruta",
        "route": "Ruta",
        "conversion_ch4_pct": "Conversion_CH4_pct",
        "conversión ch4 (%)": "Conversion_CH4_pct",
        "rendimiento_h2_mol_mol": "Rendimiento_H2_mol_mol",
        "rendimiento h2 bruto (mol/mol ch4)": "Rendimiento_H2_mol_mol",
        "fuente": "Fuente",
    }
    renamed = {col: aliases.get(str(col).strip().lower(), str(col).strip()) for col in frame.columns}
    return frame.rename(columns=renamed)


# -----------------------------------------------------------------------------
# Controles
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand"><b>H₂ <span>REFORM LAB</span></b><small>Decision support · proof of concept</small></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sidebar-status"><i></i> Núcleo termodinámico disponible</div>', unsafe_allow_html=True)
    st.markdown("### Escenario")
    route = st.radio(
        "Ruta de proceso",
        options=list(ROUTE_META),
        format_func=lambda key: f"{key} · {ROUTE_META[key]['name']}",
    )
    meta = ROUTE_META[route]
    temperature_c = st.slider("Temperatura objetivo (°C)", 500, 1000, 850, 10)
    pressure_bar = st.slider("Presión del reactor (bar)", 1.0, 30.0, 3.0, 1.0)
    ratio = st.slider(
        meta["ratio_label"],
        float(meta["ratio_range"][0]),
        float(meta["ratio_range"][1]),
        float(meta["ratio_default"]),
        float(meta["ratio_step"]),
    )
    sweep_range = st.slider("Ventana de sensibilidad (°C)", 500, 1000, (550, 1000), 25)

    with st.expander("Separación y carbono", expanded=False):
        recovery_pct = st.slider("Recuperación de H₂ (%)", 70, 99, 90, 1)
        capture_pct = st.slider("Captura de carbono potencial (%)", 0, 95, 0, 5)
        heat_source = st.selectbox(
            "Fuente de calor",
            ["Gas natural", "Electricidad renovable", "Factor personalizado"],
            help="Factor aplicado solo a demanda térmica positiva.",
        )
        if heat_source == "Gas natural":
            heat_factor = 0.202
            st.caption("0.202 kgCO₂e/kWhₜₕ · supuesto editable")
        elif heat_source == "Electricidad renovable":
            heat_factor = 0.020
            st.caption("0.020 kgCO₂e/kWhₜₕ · escenario ilustrativo")
        else:
            heat_factor = st.number_input(
                "kgCO₂e/kWhₜₕ", min_value=0.0, max_value=1.5, value=0.20, step=0.01, format="%.3f"
            )
    st.markdown("---")
    st.caption("Base: 1 mol CH₄ · gas ideal · estado isotérmico. Los resultados son de screening.")

recovery = recovery_pct / 100.0
capture_rate = capture_pct / 100.0
accent = meta["accent"]

# Cálculos principales
operating = solve_equilibrium(route, temperature_c, pressure_bar, ratio)
metrics = calculate_metrics(operating, recovery, capture_rate, heat_factor)
temps = np.unique(np.append(np.arange(sweep_range[0], sweep_range[1] + 1, 25), temperature_c))
sweep = run_temperature_sweep(route, temps, pressure_bar, ratio, recovery, capture_rate, heat_factor)
composition = operating.composition_frame()

# -----------------------------------------------------------------------------
# Encabezado
# -----------------------------------------------------------------------------
st.markdown(
    f"""<div class="hero" style="--accent:{accent}">
      <div class="eyebrow">Hydrogen systems · technical screening</div>
      <h1>Simulador de reformado de metano</h1>
      <p>Prueba de concepto reproducible para explorar desempeño técnico, demanda térmica e implicaciones de carbono de SMR, DRM y POX mediante equilibrio de Gibbs.</p>
      <div class="chip-row"><span class="chip">NIST Shomate</span><span class="chip">SciPy · SLSQP</span><span class="chip">Balance C/H/O</span><span class="chip">Exportación CSV/XLSX</span><span class="chip">v0.1 · screening</span></div>
    </div>""",
    unsafe_allow_html=True,
)

status_text = "Convergencia verificada" if operating.success else "Revisar convergencia"
status_class = "status-ok" if operating.success else "status-warn"
st.markdown(
    f"""<div class="route-card" style="--accent:{accent}">
      <div><div class="route-name">{route} · {meta['name']}</div><div class="route-desc">{meta['description']}</div></div>
      <div class="reaction">{meta['reaction']}</div>
    </div>""",
    unsafe_allow_html=True,
)

summary_tab, sensitivity_tab, data_tab, method_tab = st.tabs(
    ["Resumen ejecutivo", "Sensibilidad", "Datos & validación", "Método & plan"]
)

# -----------------------------------------------------------------------------
# TAB 1 · resumen
# -----------------------------------------------------------------------------
with summary_tab:
    section_header("Punto de operación", f"{temperature_c} °C · {pressure_bar:.0f} bar · {meta['ratio_short']} {ratio:.2f}")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card(
            "Conversión de CH₄",
            f"{metrics['Conversión CH4 (%)']:.1f}%",
            "Fracción de CH₄ alimentado transformada al equilibrio",
            accent,
        )
    with c2:
        kpi_card(
            "H₂ recuperado",
            f"{metrics['Rendimiento H2 recuperado (mol/mol CH4)']:.2f}",
            f"mol/mol CH₄ · recuperación PSA {recovery_pct}%",
            "#56B4FF",
        )
    with c3:
        kpi_card(
            "Eficiencia LHV",
            f"{metrics['Eficiencia energética LHV (%)']:.1f}%",
            "H₂ recuperado / CH₄ + calor externo estimado",
            "#B99CFF",
        )
    with c4:
        kpi_card(
            "Intensidad potencial",
            f"{metrics['Intensidad CO2e potencial (kg/kg H2)']:.1f}",
            "kgCO₂e/kgH₂ · CO como CO₂ aguas abajo",
            "#FFB86B",
        )

    st.markdown(
        f"""<div class="process" style="--accent:{accent}">
        <div class="process-node"><b>01 · Alimentación</b><span>1.00 mol CH₄<br>{meta['ratio_short']} = {ratio:.2f}</span></div><div class="process-arrow">→</div>
        <div class="process-node"><b>02 · Reactor</b><span>{temperature_c} °C · {pressure_bar:.0f} bar<br>Equilibrio ideal</span></div><div class="process-arrow">→</div>
        <div class="process-node"><b>03 · Separación H₂</b><span>{metrics['Rendimiento H2 bruto (mol/mol CH4)']:.2f} mol bruto<br>{recovery_pct}% recuperación</span></div><div class="process-arrow">→</div>
        <div class="process-node"><b>04 · Gestión de C</b><span>{capture_pct}% captura<br>{metrics['CO2 asociado al calor (kg/kg H2)']:.2f} kg/kg por calor</span></div>
        </div>""",
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.45, 1.0])
    with left:
        fig_perf = go.Figure()
        fig_perf.add_trace(
            go.Scatter(
                x=sweep["Temperatura (°C)"],
                y=sweep["Conversión CH4 (%)"],
                mode="lines",
                name="Conversión CH₄",
                line={"color": accent, "width": 3},
                hovertemplate="%{x:.0f} °C<br>%{y:.1f}%<extra></extra>",
            )
        )
        fig_perf.add_trace(
            go.Scatter(
                x=sweep["Temperatura (°C)"],
                y=sweep["Rendimiento H2 recuperado (mol/mol CH4)"],
                mode="lines",
                name="H₂ recuperado",
                yaxis="y2",
                line={"color": "#56B4FF", "width": 2.5, "dash": "dot"},
                hovertemplate="%{x:.0f} °C<br>%{y:.2f} mol/mol<extra></extra>",
            )
        )
        fig_perf.add_vline(x=temperature_c, line_width=1, line_dash="dash", line_color="#dceaff")
        fig_perf.update_layout(
            title="Ventana operativa · conversión y producción",
            yaxis={"title": "Conversión CH₄ (%)", "range": [0, 105]},
            yaxis2={"title": "H₂ recuperado (mol/mol)", "overlaying": "y", "side": "right", "showgrid": False},
        )
        st.plotly_chart(style_figure(fig_perf), width="stretch", config={"displaylogo": False})

    with right:
        comp_plot = composition.query("`Salida equilibrio (mol)` > 1e-7").copy()
        colors = {"CH4": "#71859f", "H2O": "#4f7eb3", "CO": "#ffb86b", "CO2": "#ff7b72", "H2": "#2ee6a6", "O2": "#b99cff"}
        fig_comp = go.Figure(
            go.Bar(
                x=comp_plot["Salida equilibrio (mol)"],
                y=comp_plot["Especie"],
                orientation="h",
                marker_color=[colors[s] for s in comp_plot["Especie"]],
                text=comp_plot["Salida equilibrio (mol)"].map(lambda value: f"{value:.2f}"),
                textposition="outside",
                hovertemplate="%{y}: %{x:.4f} mol<extra></extra>",
            )
        )
        fig_comp.update_layout(title="Composición a la salida", xaxis_title="mol por mol CH₄ alimentado", showlegend=False)
        st.plotly_chart(style_figure(fig_comp), width="stretch", config={"displaylogo": False})

    cues = []
    if metrics["Conversión CH4 (%)"] >= 90:
        cues.append("La conversión de equilibrio supera 90% en el punto seleccionado.")
    else:
        cues.append("Existe margen termodinámico para elevar conversión mediante temperatura, composición o menor presión.")
    if route in ("SMR", "DRM") and pressure_bar >= 10:
        cues.append("La presión elevada penaliza las rutas que aumentan el número de moles gaseosos; conviene contrastar contra el costo de compresión aguas abajo.")
    if route == "SMR" and ratio < 2.0:
        cues.append("S/C < 2 requiere un análisis explícito de formación de carbono antes de recomendar operación.")
    if capture_pct:
        cues.append(f"El escenario aplica {capture_pct}% de captura al carbono potencial tras WGS/oxidación.")
    cues.append(f"Estado numérico: <span class='{status_class}'>{status_text}</span> · residual C/H/O = {operating.atom_residual:.1e} mol.")
    st.markdown("<div class='insight'><b>Lectura técnica.</b> " + " ".join(cues) + "</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 2 · sensibilidad
# -----------------------------------------------------------------------------
with sensitivity_tab:
    section_header("Análisis paramétrico", "Cómo cambian eficiencia, carbono, temperatura y presión")
    s1, s2 = st.columns(2)
    with s1:
        fig_energy = go.Figure()
        fig_energy.add_trace(
            go.Scatter(
                x=sweep["Temperatura (°C)"],
                y=sweep["Eficiencia energética LHV (%)"],
                mode="lines+markers",
                name="Eficiencia LHV",
                line={"color": "#b99cff", "width": 2.5},
                marker={"size": 5},
            )
        )
        fig_energy.add_trace(
            go.Scatter(
                x=sweep["Temperatura (°C)"],
                y=sweep["Demanda térmica (kJ/mol CH4)"],
                mode="lines",
                name="Demanda térmica",
                yaxis="y2",
                line={"color": "#ffb86b", "width": 2, "dash": "dot"},
            )
        )
        fig_energy.update_layout(
            title="Eficiencia y carga térmica",
            yaxis={"title": "Eficiencia LHV (%)"},
            yaxis2={"title": "kJ/mol CH₄", "overlaying": "y", "side": "right", "showgrid": False},
        )
        st.plotly_chart(style_figure(fig_energy), width="stretch", config={"displaylogo": False})

    with s2:
        fig_carbon = go.Figure()
        fig_carbon.add_trace(
            go.Scatter(
                x=sweep["Temperatura (°C)"],
                y=sweep["CO2 potencial de proceso (kg/kg H2)"] * (1 - capture_rate),
                mode="lines",
                stackgroup="one",
                name="Proceso residual",
                line={"color": "#ff7b72", "width": 1},
            )
        )
        fig_carbon.add_trace(
            go.Scatter(
                x=sweep["Temperatura (°C)"],
                y=sweep["CO2 asociado al calor (kg/kg H2)"],
                mode="lines",
                stackgroup="one",
                name="Fuente de calor",
                line={"color": "#ffb86b", "width": 1},
            )
        )
        fig_carbon.update_layout(title="Desglose de intensidad potencial", yaxis_title="kgCO₂e/kgH₂")
        st.plotly_chart(style_figure(fig_carbon), width="stretch", config={"displaylogo": False})

    pressure_grid = [1, 5, 10, 20, 30]
    heat_temps = np.arange(max(500, sweep_range[0]), min(1000, sweep_range[1]) + 1, 50)
    z = []
    for p in pressure_grid:
        p_sweep = run_temperature_sweep(route, heat_temps, p, ratio, recovery, capture_rate, heat_factor)
        z.append(p_sweep["Conversión CH4 (%)"].to_list())
    fig_heat = go.Figure(
        go.Heatmap(
            x=heat_temps,
            y=pressure_grid,
            z=z,
            colorscale=[[0, "#12243a"], [0.45, "#176c71"], [1, accent]],
            colorbar={"title": "X CH₄ (%)", "thickness": 12},
            hovertemplate="T %{x:.0f} °C<br>P %{y:.0f} bar<br>X %{z:.1f}%<extra></extra>",
        )
    )
    fig_heat.add_trace(
        go.Scatter(
            x=[temperature_c], y=[pressure_bar], mode="markers", name="Punto actual",
            marker={"size": 12, "color": "#ffffff", "symbol": "x", "line": {"width": 2}},
            hovertemplate="Escenario actual<extra></extra>",
        )
    )
    fig_heat.update_layout(title="Mapa de conversión CH₄ · efecto combinado T–P", xaxis_title="Temperatura (°C)", yaxis_title="Presión (bar)")
    st.plotly_chart(style_figure(fig_heat, 430), width="stretch", config={"displaylogo": False})
    st.caption("El mapa mantiene constante la relación de alimentación, recuperación, captura y factor de calor seleccionados.")

# -----------------------------------------------------------------------------
# TAB 3 · datos y validación
# -----------------------------------------------------------------------------
with data_tab:
    section_header("Trazabilidad", "Datos del modelo, exportación y comparación con CSV/Aspen")
    d1, d2 = st.columns([1.3, 1.0])
    with d1:
        st.markdown("##### Barrido simulado")
        display_cols = [
            "Temperatura (°C)",
            "Conversión CH4 (%)",
            "Rendimiento H2 bruto (mol/mol CH4)",
            "Eficiencia energética LHV (%)",
            "Demanda térmica (kJ/mol CH4)",
            "Intensidad CO2e potencial (kg/kg H2)",
            "Convergencia",
        ]
        st.dataframe(
            sweep[display_cols].style.format(
                {
                    "Temperatura (°C)": "{:.0f}",
                    "Conversión CH4 (%)": "{:.2f}",
                    "Rendimiento H2 bruto (mol/mol CH4)": "{:.3f}",
                    "Eficiencia energética LHV (%)": "{:.2f}",
                    "Demanda térmica (kJ/mol CH4)": "{:.2f}",
                    "Intensidad CO2e potencial (kg/kg H2)": "{:.2f}",
                }
            ),
            width="stretch",
            height=390,
        )
    with d2:
        st.markdown("##### Paquete reproducible")
        st.write("Cada exportación conserva entradas, supuestos, composición y referencias del escenario activo.")
        inputs = {
            "Ruta": route,
            "Temperatura objetivo (°C)": temperature_c,
            "Presión (bar)": pressure_bar,
            meta["ratio_short"]: ratio,
            "Recuperación H2 (%)": recovery_pct,
            "Captura potencial (%)": capture_pct,
            "Fuente de calor": heat_source,
            "Factor calor (kgCO2e/kWh_th)": heat_factor,
            "Residual elemental (mol)": operating.atom_residual,
        }
        st.download_button(
            "Descargar barrido · CSV",
            data=sweep.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"{route.lower()}_barrido_temperatura.csv",
            mime="text/csv",
            width="stretch",
        )
        st.download_button(
            "Descargar paquete auditado · XLSX",
            data=excel_package(sweep, composition, inputs),
            file_name=f"{route.lower()}_paquete_reproducible.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )
        st.markdown(
            f"""<div class="insight"><b>Control de calidad.</b><br>
            Solver: {'OK' if operating.success else 'REVISAR'}<br>
            Residual elemental: {operating.atom_residual:.2e} mol<br>
            Especies: {', '.join(SPECIES)}<br>
            Dominio UI: 500–1000 °C · 1–30 bar</div>""",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("##### Comparar con experimento o tabla de sensibilidad Aspen")
    template = pd.DataFrame(
        {
            "Temperatura_C": [650, 750, 850],
            "Presion_bar": [pressure_bar] * 3,
            "Ratio": [ratio] * 3,
            "Ruta": [route] * 3,
            "Conversion_CH4_pct": [np.nan] * 3,
            "Rendimiento_H2_mol_mol": [np.nan] * 3,
            "Fuente": ["ID de estudio / Aspen case"] * 3,
        }
    )
    u1, u2 = st.columns([1.5, 1.0])
    with u1:
        uploaded = st.file_uploader(
            "CSV experimental o de simulación",
            type=["csv"],
            help="Se aceptan encabezados en español o los nombres de la plantilla.",
        )
    with u2:
        st.download_button(
            "Descargar plantilla CSV",
            template.to_csv(index=False).encode("utf-8-sig"),
            "plantilla_validacion_reformado.csv",
            "text/csv",
            width="stretch",
        )

    if uploaded is None:
        st.info("Carga un CSV para calcular predicción, error y gráfico de paridad. La aplicación no inventa datos de literatura.")
        st.dataframe(template, width="stretch", hide_index=True)
    else:
        try:
            measured = normalize_upload(pd.read_csv(uploaded))
            required = ["Temperatura_C", "Presion_bar", "Ratio"]
            missing = [c for c in required if c not in measured.columns]
            if missing:
                st.error("Faltan columnas obligatorias: " + ", ".join(missing))
            elif len(measured) > 500:
                st.error("El PoC limita la validación interactiva a 500 filas por archivo.")
            else:
                if "Ruta" not in measured:
                    measured["Ruta"] = route
                predictions = []
                for _, row in measured.iterrows():
                    row_route = str(row["Ruta"]).upper().strip()
                    if row_route not in ROUTE_META:
                        row_route = route
                    result_i = solve_equilibrium(
                        row_route,
                        round(float(row["Temperatura_C"]), 4),
                        round(float(row["Presion_bar"]), 4),
                        round(float(row["Ratio"]), 4),
                    )
                    metric_i = calculate_metrics(result_i, 1.0, 0.0, heat_factor)
                    predictions.append(
                        {
                            "Pred_Conversion_CH4_pct": metric_i["Conversión CH4 (%)"],
                            "Pred_Rendimiento_H2_mol_mol": metric_i["Rendimiento H2 bruto (mol/mol CH4)"],
                            "Solver_OK": result_i.success,
                        }
                    )
                validated = pd.concat([measured.reset_index(drop=True), pd.DataFrame(predictions)], axis=1)
                if "Conversion_CH4_pct" in validated:
                    validated["Residual_Conversion_pp"] = (
                        pd.to_numeric(validated["Conversion_CH4_pct"], errors="coerce")
                        - validated["Pred_Conversion_CH4_pct"]
                    )
                    parity = validated.dropna(subset=["Conversion_CH4_pct"])
                    if not parity.empty:
                        fig_parity = go.Figure()
                        fig_parity.add_trace(
                            go.Scatter(
                                x=parity["Pred_Conversion_CH4_pct"],
                                y=parity["Conversion_CH4_pct"],
                                mode="markers",
                                marker={"size": 9, "color": accent, "line": {"color": "#eaf2ff", "width": 1}},
                                text=parity.get("Fuente", pd.Series([""] * len(parity))),
                                hovertemplate="Modelo %{x:.1f}%<br>Dato %{y:.1f}%<br>%{text}<extra></extra>",
                            )
                        )
                        fig_parity.add_trace(go.Scatter(x=[0, 100], y=[0, 100], mode="lines", line={"color": "#71859f", "dash": "dash"}, name="1:1"))
                        fig_parity.update_layout(title="Paridad · conversión CH₄", xaxis_title="Modelo (%)", yaxis_title="Dato (%)", xaxis={"range": [0, 102]}, yaxis={"range": [0, 102]})
                        st.plotly_chart(style_figure(fig_parity, 410), width="stretch", config={"displaylogo": False})
                st.dataframe(validated, width="stretch", hide_index=True)
                st.download_button(
                    "Descargar comparación con residuales",
                    validated.to_csv(index=False).encode("utf-8-sig"),
                    "validacion_modelo.csv",
                    "text/csv",
                )
        except Exception as exc:
            st.error(f"No fue posible procesar el archivo: {exc}")

# -----------------------------------------------------------------------------
# TAB 4 · metodología, alcance y plan
# -----------------------------------------------------------------------------
with method_tab:
    section_header("Hoja de ruta", "Cuatro fases para convertir el PoC en un estudio publicable")
    phases = [
        ("FASE 01 · SEMANA 1", "Revisión & recopilación", "Matriz curada de SMR/DRM/POX: catalizador, T, P, composición, conversión, rendimiento, incertidumbre y DOI."),
        ("FASE 02 · SEMANA 2", "Modelo & simulación", "Validar Gibbs; integrar cinética Xu–Froment/PFR, coque, energía y casos Aspen con pruebas unitarias."),
        ("FASE 03 · SEMANA 3", "Dashboard interactivo", "Conectar datos y modelos, añadir escenarios, comparación, exportación reproducible y control de calidad."),
        ("FASE 04 · SEMANA 4", "Síntesis científica", "Cruzar resultados con literatura, documentar limitaciones y preparar tablas/figuras para reporte o manuscrito."),
    ]
    phase_cols = st.columns(4)
    for col, (num, title, body) in zip(phase_cols, phases):
        with col:
            st.markdown(
                f'<div class="phase" style="--accent:{accent}"><div class="phase-num">{num}</div><h4>{title}</h4><p>{body}</p></div>',
                unsafe_allow_html=True,
            )

    section_header("Arquitectura técnica", "Separación clara entre interfaz, ciencia, datos y entregables")
    st.markdown(
        f"""<div class="arch" style="--accent:{accent}">
        <div class="arch-box"><b>01 · Streamlit UI</b><span>Controles, estado del escenario, KPIs y validación de entradas</span></div><div class="arch-arrow">→</div>
        <div class="arch-box"><b>02 · Core científico</b><span>Shomate + minimización Gibbs + balances elementales + métricas</span></div><div class="arch-arrow">→</div>
        <div class="arch-box"><b>03 · Data layer</b><span>CSV/Aspen, matriz bibliográfica, limpieza y comparación</span></div><div class="arch-arrow">→</div>
        <div class="arch-box"><b>04 · Reporting</b><span>Plotly, tablas, CSV, XLSX y figuras listas para revisión</span></div>
        </div>""",
        unsafe_allow_html=True,
    )

    m1, m2 = st.columns([1.15, 1.0])
    with m1:
        st.markdown("##### Formulación implementada")
        st.latex(r"\min_{n_i}\; G = \sum_i n_i\left[g_i^\circ(T) + RT\ln\left(y_iP/P^\circ\right)\right]")
        st.latex(r"\mathbf{A}\,\mathbf{n}_{out}=\mathbf{A}\,\mathbf{n}_{feed},\qquad n_i\geq0")
        st.write(
            "Se minimiza la energía libre de una mezcla gaseosa ideal de CH₄, H₂O, CO, CO₂, H₂ y O₂. "
            "Las propiedades estándar se calculan con ecuaciones de Shomate y el problema se resuelve con SLSQP."
        )
        st.markdown(
            f"**Verificación del escenario:** residual elemental máximo = `{operating.atom_residual:.3e} mol`; "
            f"estado = **{'convergente' if operating.success else 'revisar'}**."
        )

    with m2:
        st.markdown("##### Frontera de validez")
        st.markdown(
            """
- **Sí incluye:** equilibrio T–P, composición de alimentación, balances C/H/O, demanda térmica de reacción, recuperación de H₂ y captura conceptual.
- **No incluye:** cinética/catalizador, transferencia de masa/calor, caída de presión, inertes, compresión, PSA detallada ni integración térmica.
- **Calor:** la demanda es solo el ΔH de reacción con alimentación y salida a la misma T; no incluye precalentamiento ni vaporización.
- **Coque:** C(s) no está en el conjunto de especies; el dashboard **no predice deposición de carbono**.
- **Carbono:** la intensidad potencial trata CO como CO₂ aguas abajo; no es un ACV cradle-to-gate.
- **Uso:** comparación y definición de experimentos, no dimensionamiento ni garantía de desempeño.
"""
        )

    with st.expander("Supuestos, ecuaciones auxiliares y criterios de integridad académica", expanded=False):
        st.markdown(
            """
1. Reactor isotérmico, estado estacionario, mezcla gaseosa ideal y sin caída de presión.  
2. Base de cálculo de 1 mol de CH₄; SMR usa H₂O, DRM usa CO₂ y POX usa O₂ puro.  
3. La eficiencia LHV se define como energía LHV del H₂ recuperado dividida por LHV del CH₄ más calor endotérmico de reacción, corregido por 90% de eficiencia del calentador. No se incluye calor sensible ni vaporización.  
4. El factor de la fuente de calor es un **input de escenario**, no un resultado del modelo.  
5. La captura se aplica al carbono convertido representado como CO + CO₂; deben modelarse WGS, separación y almacenamiento para un estudio completo.  
6. Los datos cargados nunca se etiquetan como literatura validada automáticamente. Cada registro debe conservar DOI/fuente, catalizador, método e incertidumbre.  
7. Antes de publicar: validación independiente, análisis de incertidumbre/sensibilidad, versionado de datos y revisión por un especialista.
"""
        )

    section_header("Base bibliográfica inicial", "Fuentes que anclan propiedades, cinética y contexto de reformado")
    references = pd.read_csv(APP_DIR / "data" / "literature_matrix.csv")
    st.dataframe(
        references,
        width="stretch",
        hide_index=True,
        column_config={"URL": st.column_config.LinkColumn("Enlace", display_text="Abrir fuente")},
    )
    st.caption("La matriz es un punto de partida del PoC. La fase 1 debe ampliar, cribar y documentar calidad, catalizador y dominio experimental.")

    st.markdown(
        """<div class="footer-note"><b>H₂ Reform Lab · v0.1</b><br>
        Prueba de concepto orientada a una propuesta de investigación. Los resultados son reproducibles con el código incluido, pero requieren validación con datos experimentales o simulación de proceso antes de sustentar decisiones de ingeniería.</div>""",
        unsafe_allow_html=True,
    )
