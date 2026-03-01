# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import math
import os

# =================================================================
# 1. CONFIGURACIÓN CORPORATIVA Y ESTILO
# =================================================================
st.set_page_config(page_title="AccuraWall 3.1 | Proyectos Estructurales", layout="wide")

st.markdown("""
    <style>
    .main > div { padding-left: 2.5rem; padding-right: 2.5rem; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #dee2e6; }
    .result-box { 
        background-color: #f0f7ff; 
        padding: 25px; 
        border-left: 10px solid #003366; 
        border-radius: 8px; 
        margin: 20px 0;
    }
    .sidebar .sidebar-content { background-color: #f2f4f7; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ AccuraWall 3.1: Prediseño de Mullions")
st.markdown("#### **Análisis de Inercia y Flexo-compresión según ASD**")
st.divider()

# =================================================================
# 2. SIDEBAR: PARÁMETROS TÉCNICOS (Basados en tu código VB)
# =================================================================
st.sidebar.header("⚙️ Parámetros de Diseño")

with st.sidebar.expander("📐 Geometría y Carga", expanded=True):
    proyecto = st.text_input("Proyecto", value="IQ Apartments")
    item_nom = st.text_input("Ítem", value="Mullion Frontal")
    L = st.number_input("Largo Mullion (L) [mm]", value=3500.0)
    B = st.number_input("Ancho Tributario (B) [mm]", value=1500.0)
    q = st.number_input("Viento (q) [kgf/m²]", value=100.0)
    e_vidrio = st.number_input("Espesor Cristal (mm)", value=6.0)

with st.sidebar.expander("🧪 Material y Seguridad", expanded=True):
    material = st.selectbox("Material", 
                           ["Aluminio 6063 - T6", "Aluminio 6063 - T5", "Acero A42-27ES"])
    # Criterio de deflexión (L/175 o L/240)
    criterio_d = st.selectbox("Criterio de Deflexión", ["L/175", "L/240", "19.05 mm (fijo)"])
    esbeltez_max = st.number_input("Esbeltez Límite", value=300.0)

distribucion = st.sidebar.radio("Distribución de Carga Tributaria", 
                               ["Rectangular (Simplificada)", "Trapezoidal (Real)"],
                               help="La carga trapezoidal considera la distribución real de esfuerzos según el ancho tributario.")

# =================================================================
# 3. MOTOR DE CÁLCULO REVISADO
# =================================================================

def calcular_mullion():
    # Propiedades de Materiales (Valores exactos de tu VB)
    if material == "Aluminio 6063 - T6":
        E_kgm2, Fcy_kgm2 = 7.101e9, 1.757e7
    elif material == "Aluminio 6063 - T5":
        E_kgm2, Fcy_kgm2 = 7.101e9, 1.124e7
    else: # Acero
        E_kgm2, Fcy_kgm2 = 2.1e10, 2.753e7

    # Conversión a kgf y m para el cálculo interno
    L_m, B_m = L / 1000, B / 1000
    
    # 1. CARGA AXIAL (N) - Incluye peso propio estimado
    N = (e_vidrio * B_m * L_m * 2500) / 1000 + (B_m * L_m * 5) + (L_m * 20)

    # 2. MOMENTO FLECTOR (M)
    M = (1/8) * (q * B_m) * (L_m**2)

    # 3. DEFLEXIÓN ADMISIBLE (Df)
    if criterio_d == "L/175":
        Df_m = L_m / 175
    elif criterio_d == "L/240":
        Df_m = L_m / 240
    else:
        Df_m = 19.05 / 1000

    # 4. INERCIA REQUERIDA (Ix)
    if distribucion == "Rectangular (Simplificada)":
        # Fórmula estándar de viga simplemente apoyada con carga uniforme
        I_req_m4 = (5/384) * (q * B_m * L_m**4) / (E_kgm2 * Df_m)
    else:
        # LÓGICA TRAPEZOIDAL REVISADA
        # Basada en el Boletín Técnico de Diseño Estructural
        # Factor = (1 - 4/3 * (B/2L)^2)
        ratio = B_m / (2 * L_m)
        factor_trapezoidal = (1 - (4/3) * (ratio**2))
        I_req_m4 = ((5/384) * (q * B_m * L_m**4) / (E_kgm2 * Df_m)) * factor_trapezoidal

    # 5. MÓDULO RESISTENTE (Sx)
    # Según ASD (Tensión admisible = 0.6 * Fy)
    Fb = 0.6 * Fcy_kgm2
    S_req_m3 = M / Fb

    return N, I_req_m4 * (100**4), S_req_m3 * (100**3)

axial, inercia, modulo = calcular_mullion()

# =================================================================
# 4. DESPLIEGUE DE RESULTADOS
# =================================================================
st.subheader(f"📊 Resultados de Prediseño: {item_nom}")

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Inercia Mínima (Ix)", f"{inercia:.2f} cm⁴")
with c2:
    st.metric("Módulo Resistente (Sx)", f"{modulo:.2f} cm³")
with c3:
    st.metric("Carga Axial Est.", f"{axial:.2f} kgf")



st.markdown(f"""
<div class="result-box">
    <h3>✅ Especificación Técnica:</h3>
    <p>Proyecto: <strong>{proyecto}</strong> | Método: <strong>ASD</strong></p>
    <hr>
    <ul>
        <li><strong>Inercia Requerida:</strong> {inercia:.2f} cm⁴ (Gobernada por {criterio_d})</li>
        <li><strong>Distribución:</strong> {distribucion}</li>
        <li><strong>Material:</strong> {material}</li>
    </ul>
    <p><small>Nota: Los cálculos consideran apoyos simples en los extremos. Para mullions continuos, la inercia puede reducirse según análisis de vanos.</small></p>
</div>
""", unsafe_allow_html=True)

# =================================================================
# 5. GRÁFICO DE COMPARACIÓN DE DISTRIBUCIÓN
# =================================================================
st.subheader("📈 Comparativa de Métodos de Carga")

# Generar datos comparativos
L_axis = np.linspace(2000, 5000, 30)
I_rect = []
I_trap = []

for l_val in L_axis:
    l_m = l_val / 1000
    df_m = l_m / 175
    E_val = 7.101e9 if material.startswith("Aluminio") else 2.1e10
    
    # Rectangular
    i_r = (5/384) * (q * (B/1000) * l_m**4) / (E_val * df_m)
    I_rect.append(i_r * 100**4)
    
    # Trapezoidal
    ratio = (B/1000) / (2 * l_m)
    i_t = i_r * (1 - (4/3)*(ratio**2))
    I_trap.append(i_t * 100**4)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(L_axis, I_rect, color='#d9534f', ls='--', label='Distribución Rectangular (Conservadora)')
ax.plot(L_axis, I_trap, color='#003366', lw=2, label='Distribución Trapezoidal (Real)')
ax.scatter([L], [inercia], color='black', zorder=5)
ax.set_xlabel("Largo del Mullion (mm)")
ax.set_ylabel("Ix Requerida (cm⁴)")
ax.set_title("Efecto del Área Tributaria en la Inercia")
ax.legend()
ax.grid(True, alpha=0.3)
st.pyplot(fig)

# =================================================================
# 6. CIERRE
# =================================================================
st.markdown("---")
st.markdown(f"""
    <div style="text-align: center; color: #666; font-size: 0.85em;">
        <strong>Structural Lab | Mauricio Riquelme</strong><br>
        <em>"Programming is understanding"</em>
    </div>
""", unsafe_allow_html=True)