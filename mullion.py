# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import math
import os

# =================================================================
# 1. CONFIGURACIÓN Y ESTILO
# =================================================================
st.set_page_config(page_title="AccuraWall | Mauricio Riquelme", layout="wide")

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
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ AccuraWall: Prediseño de Mullions")
st.markdown("#### **Criterio de Deflexión Automatizado L/175 - L/240 + 6.35mm**")
st.divider()

# =================================================================
# 2. SIDEBAR: PARÁMETROS TÉCNICOS
# =================================================================
st.sidebar.header("⚙️ Parámetros de Diseño")

with st.sidebar.expander("📐 Geometría y Carga", expanded=True):
    L = st.number_input("Alto del Mullion (L) [mm]", value=3500.0, step=10.0)
    B = st.number_input("Ancho Tributario (B) [mm]", value=1500.0, step=10.0)
    q = st.number_input("Carga de Viento (q) [kgf/m²]", value=100.0, step=5.0)
    e_vidrio = st.number_input("Espesor Cristal (e) [mm]", value=6.0)

# Lógica del criterio de deformación automática
if L < 4115:
    criterio_sugerido = f"L/175"
    valor_df_sugerido = L / 175
else:
    criterio_sugerido = f"L/240 + 6.35"
    valor_df_sugerido = (L / 240) + 6.35

with st.sidebar.expander("📏 Criterio de Deformación", expanded=True):
    st.markdown(f"**Sugerido por Norma:** `{criterio_sugerido}`")
    # Casilla editable para la deflexión admisible
    df_admisible = st.number_input("Deflexión Admisible [mm] (Editable)", 
                                    value=float(valor_df_sugerido), 
                                    help="Este valor se calcula automáticamente según L, pero puedes editarlo.")

with st.sidebar.expander("🧪 Material", expanded=True):
    material = st.selectbox("Material", 
                           ["Aluminio 6063 - T6", "Aluminio 6063 - T5", "Acero A42-27ES"])
    distribucion = st.radio("Distribución de Carga", 
                               ["Rectangular (Simplificada)", "Trapezoidal (Real)"])

# =================================================================
# 3. MOTOR DE CÁLCULO
# =================================================================
def calcular_requerimientos():
    # Propiedades según tu código VB
    if material == "Aluminio 6063 - T6":
        E, Fcy = 7101002754, 17576739.5
    elif material == "Aluminio 6063 - T5":
        E, Fcy = 7101002754, 11249113.3
    else: # Acero
        E, Fcy = 21000000000, 27532337.75

    L_m = L / 1000
    B_m = B / 1000
    Df_m = df_admisible / 1000 # Usa el valor de la casilla editable

    # Carga Axial (N)
    N = (e_vidrio * B_m * L_m * 2500) / 1000**3 + (B_m * L_m * 5) / 1000**2 + (L_m * 20) / 1000
    
    # Momento Flector (M)
    M = (1/8) * (q * B_m) * (L_m)**2

    # Inercia Requerida (Ix)
    if distribucion == "Rectangular (Simplificada)":
        I_req = (5 / 384) * q * B_m * L_m**4 / (E * Df_m)
    else:
        # Ajuste Trapezoidal
        ratio = B_m / (2 * L_m)
        factor = (1 - (4/3) * (ratio**2))
        I_req = ((5 / 384) * q * B_m * L_m**4 / (E * Df_m)) * factor

    # Módulo Resistente (Sx)
    Fb = 0.6 * Fcy
    S_req = M / Fb

    return I_req * 100**4, S_req * 100**3

inercia, modulo = calcular_requerimientos()

# =================================================================
# 4. DESPLIEGUE DE RESULTADOS
# =================================================================
st.subheader("📊 Requerimientos Mínimos de Sección")

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Inercia (Ix)", f"{inercia:.2f} cm⁴")
with c2:
    st.metric("Módulo (Sx)", f"{modulo:.2f} cm³")
with c3:
    st.metric("Límite Δ", f"{df_admisible:.2f} mm", delta=criterio_sugerido)



st.markdown(f"""
<div class="result-box">
    <h3>✅ Especificación Técnica:</h3>
    <ul>
        <li><strong>Longitud del elemento:</strong> {L} mm</li>
        <li><strong>Criterio aplicado:</strong> {criterio_sugerido} (Deflexión máx: {df_admisible:.2f} mm)</li>
        <li><strong>Inercia mínima requerida:</strong> {inercia:.2f} cm⁴</li>
        <li><strong>Módulo resistente mínimo:</strong> {modulo:.2f} cm³</li>
    </ul>
    <p><small>Nota: Se ha detectado automáticamente el umbral de 4115 mm para el cambio de criterio normativo.</small></p>
</div>
""", unsafe_allow_html=True)

# =================================================================
# 5. GRÁFICO DE SENSIBILIDAD
# =================================================================
st.subheader("📈 Comportamiento de Inercia vs Altura")
L_axis = np.linspace(2000, 6000, 50)
I_axis = []

for lx in L_axis:
    # Aplicar el cambio de criterio en la curva del gráfico
    if lx < 4115:
        dfx = lx / 175
    else:
        dfx = (lx / 240) + 6.35
    
    if material.startswith("Aluminio"):
        E_x = 7101002754
    else:
        E_x = 21000000000
    
    ix = (5 / 384) * q * (B/1000) * (lx/1000)**4 / (E_x * (dfx/1000))
    I_axis.append(ix * 100**4)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(L_axis, I_axis, color='#003366', label='Ix Requerida (Curva Normativa)')
ax.axvline(4115, color='red', ls='--', alpha=0.5, label='Umbral 4115mm')
ax.scatter([L], [inercia], color='red', zorder=5)
ax.set_xlabel("Longitud L (mm)")
ax.set_ylabel("Ix (cm4)")
ax.legend()
ax.grid(True, alpha=0.3)
st.pyplot(fig)

# 6. CIERRE
st.markdown("---")
st.markdown(f"""
    <div style="text-align: center; color: #666; font-size: 0.8em;">
        <strong>Structural Lab | Mauricio Riquelme</strong><br>
        <em>"Programming is understanding"</em>
    </div>
""", unsafe_allow_html=True)