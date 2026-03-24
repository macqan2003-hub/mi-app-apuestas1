import streamlit as st
import requests
import pandas as pd
import numpy as np  # <--- ESTA ES LA LÍNEA QUE FALTA
import plotly.graph_objects as go
from datetime import datetime
# Configuración de página
st.set_page_config(page_title="Radar de Valor Pro", layout="wide")

# Estilo para las alertas (CSS)
st.markdown("""
    <style>
    .stAlert {
        border: 2px solid #00ff00;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0px rgba(0, 255, 0, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(0, 255, 0, 0); }
        100% { box-shadow: 0 0 0 0px rgba(0, 255, 0, 0); }
    }
    </style>
    """, unsafe_allow_html=True)

# Inicializar historial
if 'historial' not in st.session_state:
    st.session_state.historial = []

# --- CONFIGURACIÓN LATERAL ---
st.sidebar.header("🕹️ Panel de Control")
api_key = st.sidebar.text_input("Tu API Key:", value="67d6ea7050cf2cd71bfe7032048320ba")
bankroll = st.sidebar.number_input("Capital (€):", value=1000)
edge_min = st.sidebar.slider("Ventaja Mínima (Edge %):", 1.0, 10.0, 3.0) / 100

# Diccionario de ligas para el escáner masivo
DICCIONARIO_LIGAS = {
    "La Liga (ESP)": "soccer_spain_la_liga",
    "Premier League (UK)": "soccer_epl",
    "Bundesliga (GER)": "soccer_germany_bundesliga",
    "Serie A (ITA)": "soccer_italy_serie_a",
    "Champions League": "soccer_uefa_champs_league",
    "NBA (USA)": "basketball_nba",
    "Segunda España": "soccer_spain_segunda_division"
}

# --- FUNCIÓN DE ESCANEO CORE ---
def escanear_liga(key, liga_id, edge_m):
    url = f"https://api.the-odds-api.com/v4/sports/{liga_id}/odds/"
    params = {"apiKey": key, "regions": "eu", "markets": "h2h"}
    try:
        res = requests.get(url, params=params).json()
        encontrados = []
        for partido in res:
            if not partido['bookmakers']: continue
            home, away = partido['home_team'], partido['away_team']
            odds = partido['bookmakers'][0]['markets'][0]['outcomes']
            
            # Cuotas y cálculo de Margen
            try:
                c_h = next(o['price'] for o in odds if o['name'] == home)
                c_a = next(o['price'] for o in odds if o['name'] == away)
                try:
                    c_d = next(o['price'] for o in odds if o['name'] == "Draw")
                    margin = (1/c_h) + (1/c_a) + (1/c_d)
                except: margin = (1/c_h) + (1/c_a)

                prob_h = (1/c_h) / margin
                edge = (c_h * prob_h) - 1

                if edge > edge_m:
                    stake = round(((c_h * prob_h - 1) / (c_h - 1)) * 0.25 * bankroll, 2)
                    encontrados.append({
                        "Liga": liga_id,
                        "Partido": f"{home} vs {away}",
                        "Pick": home,
                        "Cuota": c_h,
                        "Edge": f"{round(edge*100, 2)}%",
                        "Stake (€)": stake,
                        "Casa": partido['bookmakers'][0]['title']
                    })
            except: continue
        return encontrados
    except: return []

# --- INTERFAZ ---
st.title("📡 Radar de Valor Inteligente")

# BOTÓN DE ESCANEO MASIVO
if st.button("🔥 ESCANEO MASIVO (Todas las Ligas)"):
    todas_ops = []
    progreso = st.progress(0)
    
    for i, (nombre, liga_id) in enumerate(DICCIONARIO_LIGAS.items()):
        ops = escanear_liga(api_key, liga_id, edge_min)
        todas_ops.extend(ops)
        progreso.progress((i + 1) / len(DICCIONARIO_LIGAS))
    
    if todas_ops:
        st.balloons() # Animación de éxito
        st.success(f"⚠️ ¡ALERTA! Se han encontrado {len(todas_ops)} oportunidades con valor real.")
        
        df = pd.DataFrame(todas_ops)
        st.table(df)
        
        # Alerta visual persistente
        for op in todas_ops:
            st.toast(f"¡VALOR DETECTADO! {op['Partido']}", icon="💰")
    else:
        st.warning("Mercado analizado. No hay valor positivo en este momento.")

# Pestañas para historial y proyecciones
tab1, tab2 = st.tabs(["📉 Historial Real", "📊 Simulación de Interés Compuesto"])

with tab1:
    st.write("Registra tus apuestas aquí para medir tu rentabilidad.")
    # (Aquí iría la lógica de guardado que ya teníamos)

with tab2:
    # Gráfica de proyección profesional
    st.subheader("Tu camino a la rentabilidad")
    puntos = [bankroll]
    for _ in range(50):
        ganada = np.random.rand() < 0.52 # Probabilidad conservadora
        cambio = (puntos[-1] * 0.02 * 0.95) if ganada else -(puntos[-1] * 0.02)
        puntos.append(puntos[-1] + cambio)
    
    fig = go.Figure(data=go.Scatter(y=puntos, line=dict(color='#00ff00', width=3)))
    fig.update_layout(title="Proyección a 50 apuestas con Interés Compuesto", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)
