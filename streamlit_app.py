import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Predicciones Pro AI - Gestión Total", layout="wide")

# Inicializar el historial en la memoria de la sesión si no existe
if 'historial' not in st.session_state:
    st.session_state.historial = []

# ==========================================
# BARRA LATERAL
# ==========================================
st.sidebar.header("📊 Configuración")
api_key = st.sidebar.text_input("Tu API Key:", value="67d6ea7050cf2cd71bfe7032048320ba")
bankroll_inicial = st.sidebar.number_input("Capital Inicial (€):", value=1000)
edge_min = st.sidebar.slider("Ventaja mínima (Edge %):", 1, 15, 3) / 100

# Selección de Liga
ligas = {
    "La Liga (España)": "soccer_spain_la_liga",
    "Premier League (UK)": "soccer_epl",
    "NBA (USA)": "basketball_nba",
    "Champions League": "soccer_uefa_champs_league"
}
liga_seleccionada = st.sidebar.selectbox("Seleccionar Competición:", list(ligas.keys()))

# ==========================================
# LÓGICA DE DATOS
# ==========================================
def buscar_oportunidades(key, liga_id):
    url = f"https://api.the-odds-api.com/v4/sports/{liga_id}/odds/"
    params = {"apiKey": key, "regions": "eu", "markets": "h2h"}
    try:
        res = requests.get(url, params=params).json()
        output = []
        for partido in res:
            if not partido['bookmakers']: continue
            home, away = partido['home_team'], partido['away_team']
            odds = partido['bookmakers'][0]['markets'][0]['outcomes']
            
            # Cálculo simple de cuota justa (quitando margen)
            c_h = next(o['price'] for o in odds if o['name'] == home)
            c_a = next(o['price'] for o in odds if o['name'] == away)
            try:
                c_d = next(o['price'] for o in odds if o['name'] == "Draw")
                margin = (1/c_h) + (1/c_a) + (1/c_d)
            except: margin = (1/c_h) + (1/c_a)

            prob_h = (1/c_h) / margin
            edge = (c_h * prob_h) - 1
            
            if edge > edge_min:
                # Kelly 0.25
                stake_eur = round(((c_h * prob_h - 1) / (c_h - 1)) * 0.25 * bankroll_inicial, 2)
                output.append({
                    "Partido": f"{home} vs {away}",
                    "Pick": home,
                    "Cuota": c_h,
                    "Edge": f"{round(edge*100, 1)}%",
                    "Sugerencia": f"{stake_eur}€",
                    "id": partido['id']
                })
        return output
    except: return []

# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================
st.title("🏆 AI Sports Betting Manager")

tab1, tab2, tab3 = st.tabs(["🔍 Escáner", "📝 Mi Historial", "📈 Rendimiento"])

with tab1:
    st.subheader("Oportunidades de hoy")
    if st.button("🔄 Escanear Mercado Ahora"):
        ops = buscar_oportunidades(api_key, ligas[liga_seleccionada])
        if ops:
            for op in ops:
                with st.expander(f"📍 {op['Partido']} - {op['Edge']} de Ventaja"):
                    st.write(f"**Apuesta recomendada:** Victoria de {op['Pick']} a cuota {op['Cuota']}")
                    st.write(f"**Importe sugerido:** {op['Sugerencia']}")
                    if st.button(f"Registrar Apuesta", key=op['id']):
                        st.session_state.historial.append({
                            "Fecha": datetime.now().strftime("%d/%m/%Y"),
                            "Evento": op['Partido'],
                            "Cuota": op['Cuota'],
                            "Importe": float(op['Sugerencia'].replace('€','')),
                            "Estado": "Pendiente"
                        })
                        st.success("¡Añadida al historial!")
        else:
            st.info("No hay valor suficiente en esta liga ahora mismo.")

with tab2:
    st.subheader("Registro de mis jugadas")
    if st.session_state.historial:
        df_hist = pd.DataFrame(st.session_state.historial)
        st.table(df_hist)
        if st.button("Limpiar Historial"):
            st.session_state.historial = []
            st.rerun()
    else:
        st.write("Aún no has registrado ninguna apuesta.")

with tab3:
    st.subheader("Análisis de Beneficios")
    # Generamos una gráfica de ejemplo basada en el historial (o simulación si está vacío)
    if len(st.session_state.historial) > 0:
        st.write("Aquí verás la evolución de tu dinero real conforme marques resultados.")
    
    # Gráfica de simulación profesional (Monte Carlo)
    st.info("Simulación teórica basada en tu configuración actual:")
    puntos = [bankroll_inicial]
    for _ in range(30):
        # Simulación: 55% de acierto en cuotas 2.0
        ganada = np.random.rand() < 0.55 
        cambio = (puntos[-1] * 0.02 * 1.0) if ganada else -(puntos[-1] * 0.02)
        puntos.append(puntos[-1] + cambio)
    
    fig = go.Figure(data=go.Scatter(y=puntos, line=dict(color='#00CC96', width=3)))
    fig.update_layout(title="Proyección de Crecimiento Compuesto", xaxis_title="Nº de Apuestas", yaxis_title="Euros (€)")
    st.plotly_chart(fig, use_container_width=True)
