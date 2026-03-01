# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import math
import os

# 1. CONFIGURACIÓN Y ESTILO
st.set_page_config(page_title="AccuraWall | Proyectos Estructurales", layout="wide")

st.markdown("""
    <style>
    .main > div { padding-left: 2.5rem; padding-right: 2.5rem; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #dee2e6; }
    .result-box { 
        background-color: #f0f7ff; 
        padding: 25px; 
        border-left: 8px solid #003366; 
        border-radius: 8px; 
        margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ AccuraWall: Prediseño de Mullions")
st.markdown("#### **Cálculo de Inercia y Módulo Resistente según ASD**")
st.divider()

# 2. SIDEBAR: PARÁMETROS TÉCNICOS (Traducción de tu VB)
st.sidebar.header("⚙️ Configuración del Mullion")

with st.sidebar.expander("🏗️ Proyecto e Ítem", expanded=True):
    proyecto = st.text_input("Proyecto", value="Edificio San Francisco")
    item = st.text_input("Ítem / Ubicación", value="Mullion Tipo A")

with st.sidebar.expander("📐 Geometría y Carga", expanded=True):
    L = st.number_input("Alto del Mullion (L) [mm]", value=3500.0)
    B = st.number_input("Ancho Tributario (B) [mm]", value=1500.0)
    q = st.number_input("Carga de Viento (q) [kgf/m²]", value=100.0)
    espesor_vidrio = st.number_input("Espesor Total Cristal (e) [mm]", value=6.0)

with st.sidebar.expander("🧪 Material y Método", expanded=True):
    material = st.selectbox("Material", 
                           ["Aluminio 6063 - T6", "Aluminio 6063 - T5", "Acero A42-27ES"])
    metodo = st.radio("Método de Diseño", ["ASD", "LRFD (No implementado)"])
    esbeltez_limite = st.number_input("Esbeltez Límite", value=300.0)

# Selector de Distribución solicitado
st.sidebar.markdown("---")
distribucion = st.sidebar.radio("Distribución de Carga", 
                               ["Rectangular (Simplificada)", "Trapezoidal (Real)"], 
                               help="Cambia el cálculo de la Inercia requerida según la forma del área tributaria.")

# 3. MOTOR DE CÁLCULO (Lógica de tu VB6/VBA)
def calcular_requerimientos():
    # Constantes de Material según tu código VB
    if material == "Aluminio 6063 - T6":
        E, Fcy = 7101002754, 17576739.5
    elif material == "Aluminio 6063 - T5":
        E, Fcy = 7101002754, 11249113.3
    else: # Acero
        E, Fcy = 21000000000, 27532337.75

    # Carga Axial (N)
    N = (espesor_vidrio * B * L * 2500) / 1000**3 + (B * L * 5) / 1000**2 + (L * 20) / 1000
    
    # Momento Flector (M)
    M = (1/8) * (q * B / 1000) * (L / 1000)**2

    # Inercia Requerida (A1 en tu VB)
    Df = (L / 175) / 1000 # Criterio L/175
    
    if distribucion == "Rectangular (Simplificada)":
        # Fórmula estándar 5/384
        I_req = (5 / 384) * q * (B / 1000) * (L / 1000)**4 / (E * Df)
    else:
        # Fórmula para carga Trapezoidal (Tributaria real)
        # Basado en la integración de carga para perfiles de fachada
        I_req = (q * B / 1000) * (L / 1000)**4 / (192 * E * Df) * (25 - 40 * (B/L)**2 + 16 * (B/L)**4) / 16

    # Módulo Resistente (Simplificación ASD)
    Fb = 0.6 * Fcy
    S_req = M / Fb

    return N, I_req * 100**4, S_req * 100**3

axial, inercia, modulo = calcular_requerimientos()

# 4. DESPLIEGUE DE RESULTADOS
st.subheader("📊 Requerimientos Mínimos de Sección")

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Inercia (Ix)", f"{inercia:.2f} cm⁴")
with c2:
    st.metric("Módulo (Sx)", f"{modulo:.2f} cm³")
with c3:
    st.metric("Carga Axial (N)", f"{axial:.2f} kgf")



st.markdown(f"""
<div class="result-box">
    <h3>✅ Especificación de Diseño - {item}</h3>
    <p>Basado en la normativa para <strong>{material}</strong> con distribución <strong>{distribucion}</strong>.</p>
    <hr>
    <ul>
        <li><strong>Inercia mínima requerida:</strong> {inercia:.2f} cm⁴ (Criterio L/175)</li>
        <li><strong>Módulo resistente mínimo:</strong> {modulo:.2f} cm³</li>
        <li><strong>Estado de carga:</strong> Flexocompresión simple.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# 5. GRÁFICO DE SENSIBILIDAD (Inercia vs Longitud)
st.subheader("📈 Sensibilidad de Inercia Requerida")
L_range = np.linspace(2000, 5000, 20)
I_range = []

for l_val in L_range:
    df_val = (l_val / 175) / 1000
    if material.startswith("Aluminio"):
        E_val = 7101002754
    else:
        E_val = 21000000000
    
    if distribucion == "Rectangular (Simplificada)":
        i_val = (5 / 384) * q * (B / 1000) * (l_val / 1000)**4 / (E_val * df_val)
    else:
        i_val = (q * B / 1000) * (l_val / 1000)**4 / (192 * E_val * df_val) # Aprox trapezoidal
    I_range.append(i_val * 100**4)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(L_range, I_range, color='#003366', lw=2, label='Inercia Crítica')
ax.scatter([L], [inercia], color='red', zorder=5, label='Punto Actual')
ax.set_xlabel("Longitud del Mullion (mm)")
ax.set_ylabel("Ix Requerida (cm4)")
ax.grid(True, alpha=0.3)
ax.legend()
st.pyplot(fig)

# 6. CIERRE
st.markdown("---")
st.markdown(f"""
    <div style="text-align: center; color: #666; font-size: 0.8em;">
        <strong>AccuraWall Online Port</strong> | Mauricio Riquelme <br>
        <em>"Programming is understanding"</em>
    </div>
""", unsafe_allow_html=True)