import streamlit as st
import networkx as nx
import plotly.graph_objects as go
from PIL import Image
import math
import itertools

st.set_page_config(layout="wide")
st.title("Navegador Universitario - Mapa Interactivo")

posiciones = {
    'H': (110, 725), 'A': (405, 755), 'K': (585, 765),
    'B': (405, 620), 'G': (590, 630), 'C': (405, 500),
    'D': (315, 385), 'E': (675, 435), 'I': (315, 175), 'J': (590, 185)
}

ESCALA_METROS_POR_PIXEL = 0.5

def distancia_metros(n1, n2):
    x0, y0 = posiciones[n1]
    x1, y1 = posiciones[n2]
    return round(math.sqrt((x1-x0)**2 + (y1-y0)**2) * ESCALA_METROS_POR_PIXEL)

G = nx.Graph()
for nodo, pos in posiciones.items():
    G.add_node(nodo, pos=pos)

conexiones = [
    ('H', 'A'), ('H', 'D'), ('A', 'B'), ('A', 'K'), ('B', 'C'),
    ('B', 'G'), ('C', 'D'), ('C', 'E'), ('G', 'K'), ('G', 'E'),
    ('D', 'I'), ('I', 'J'), ('J', 'E')
]
for u, v in conexiones:
    G.add_edge(u, v, weight=distancia_metros(u, v))

if 'ruta' not in st.session_state:
    st.session_state.ruta = []
if 'distancia_total' not in st.session_state:
    st.session_state.distancia_total = 0
if 'todas_rutas' not in st.session_state:
    st.session_state.todas_rutas = []
if 'arbol_aristas' not in st.session_state:
    st.session_state.arbol_aristas = []
if 'arbol_peso_total' not in st.session_state:
    st.session_state.arbol_peso_total = 0
if 'arbol_algoritmo' not in st.session_state:
    st.session_state.arbol_algoritmo = ''
if 'todos_arboles' not in st.session_state:
    st.session_state.todos_arboles = []

def calcular_peso_ruta(ruta):
    return sum(G[ruta[i]][ruta[i+1]]['weight'] for i in range(len(ruta)-1))

col1, col2 = st.columns([1, 3])
with col1:
    origen = st.selectbox("Punto de partida:", sorted(posiciones.keys()))
    destino = st.selectbox("Destino:", sorted(posiciones.keys()))

    st.markdown("---")

    # Botón 1: ruta óptima directa
    if st.button("🗺️ Calcular Ruta"):
        st.session_state.todas_rutas = []
        try:
            st.session_state.ruta = nx.shortest_path(G, source=origen, target=destino, weight='weight')
            st.session_state.distancia_total = calcular_peso_ruta(st.session_state.ruta)
        except:
            st.session_state.ruta = []
            st.error("No hay camino")

    # Botón 2: comparar todas las rutas posibles
    if st.button("⚡ Mostrar Ruta más Corta"):
        try:
            todos = list(nx.all_simple_paths(G, source=origen, target=destino))
            if not todos:
                st.error("No hay camino")
                st.session_state.todas_rutas = []
            else:
                rutas_con_peso = sorted(
                    [(r, calcular_peso_ruta(r)) for r in todos],
                    key=lambda x: x[1]
                )
                st.session_state.todas_rutas = rutas_con_peso
                # La más corta se resalta en el mapa
                st.session_state.ruta = rutas_con_peso[0][0]
                st.session_state.distancia_total = rutas_con_peso[0][1]
        except:
            st.session_state.todas_rutas = []
            st.error("No hay camino")

    st.markdown("---")

    # Botón 3: árbol de expansión mínimo con Prim
    if st.button("🌳 Árbol de Expansión Mínimo Prim"):
        st.session_state.todos_arboles = []
        try:
            arbol = nx.minimum_spanning_tree(G, weight='weight', algorithm='prim')
            if not arbol.edges():
                st.error("No hay camino")
                st.session_state.arbol_aristas = []
            else:
                st.session_state.arbol_aristas = list(arbol.edges())
                st.session_state.arbol_peso_total = sum(
                    data['weight'] for _, _, data in arbol.edges(data=True)
                )
                st.session_state.arbol_algoritmo = 'Prim'
        except:
            st.session_state.arbol_aristas = []
            st.error("No hay camino")

    # Botón 4: árbol de expansión mínimo con Kruskal
    if st.button("🌳 Árbol de Expansión Mínimo Kruskal"):
        st.session_state.todos_arboles = []
        try:
            arbol = nx.minimum_spanning_tree(G, weight='weight', algorithm='kruskal')
            if not arbol.edges():
                st.error("No hay camino")
                st.session_state.arbol_aristas = []
            else:
                st.session_state.arbol_aristas = list(arbol.edges())
                st.session_state.arbol_peso_total = sum(
                    data['weight'] for _, _, data in arbol.edges(data=True)
                )
                st.session_state.arbol_algoritmo = 'Kruskal'
        except:
            st.session_state.arbol_aristas = []
            st.error("No hay camino")

    # Botón 5: comparar todos los árboles de expansión posibles
    if st.button("📊 Comparar Árboles de Expansión"):
        st.session_state.todos_arboles = []
        try:
            n = G.number_of_nodes()
            edges = list(G.edges())
            arboles_con_peso = []
            for combo in itertools.combinations(edges, n - 1):
                H = nx.Graph()
                H.add_nodes_from(G.nodes())
                H.add_edges_from(combo)
                if nx.is_connected(H):
                    peso = sum(G[u][v]['weight'] for u, v in combo)
                    arboles_con_peso.append((combo, peso))

            if not arboles_con_peso:
                st.error("No hay camino")
            else:
                arboles_con_peso.sort(key=lambda x: x[1])
                st.session_state.todos_arboles = arboles_con_peso
                # El más corto se resalta en el mapa
                st.session_state.arbol_aristas = list(arboles_con_peso[0][0])
                st.session_state.arbol_peso_total = arboles_con_peso[0][1]
                st.session_state.arbol_algoritmo = 'Comparación'
        except:
            st.session_state.todos_arboles = []
            st.error("No hay camino")

    if st.session_state.arbol_aristas:
        st.success(f"🌳 Árbol de expansión mínima ({st.session_state.arbol_algoritmo})")
        aristas_txt = ", ".join(f"{u}-{v}" for u, v in st.session_state.arbol_aristas)
        st.info(f"🔗 Aristas: {aristas_txt}")
        st.info(f"📏 Peso total: **{st.session_state.arbol_peso_total} m**")
        if st.button("❌ Ocultar árbol"):
            st.session_state.arbol_aristas = []
            st.session_state.arbol_peso_total = 0
            st.session_state.arbol_algoritmo = ''
            st.session_state.todos_arboles = []

    # Tabla comparativa de árboles de expansión
    if st.session_state.todos_arboles:
        total = len(st.session_state.todos_arboles)
        st.markdown(f"### 📊 Comparación de árboles de expansión ({total} en total)")
        for idx, (combo, peso) in enumerate(st.session_state.todos_arboles[:15]):
            medal = ["🥇", "🥈", "🥉"][idx] if idx < 3 else f"{idx+1}."
            label = ", ".join(f"{u}-{v}" for u, v in combo)
            if idx == 0:
                st.success(f"{medal} **{label}**  \n`{peso} m` ← MÍNIMO")
            else:
                extra = peso - st.session_state.todos_arboles[0][1]
                st.warning(f"{medal} {label}  \n`{peso} m` (+{extra} m)")
        if total > 15:
            st.caption(f"Mostrando los 15 árboles más cortos de {total} posibles.")

    st.markdown("---")

    if st.session_state.ruta:
        st.success(f"✅ Ruta: {' → '.join(st.session_state.ruta)}")
        st.info(f"📏 Distancia: **{st.session_state.distancia_total} m**")

    # Tabla comparativa de rutas
    if st.session_state.todas_rutas:
        st.markdown("### 📊 Comparación de rutas")
        for idx, (r, peso) in enumerate(st.session_state.todas_rutas):
            medal = ["🥇", "🥈", "🥉"][idx] if idx < 3 else f"{idx+1}."
            label = " → ".join(r)
            if idx == 0:
                st.success(f"{medal} **{label}**  \n`{peso} m` ← MÁS CORTA")
            else:
                extra = peso - st.session_state.todas_rutas[0][1]
                st.warning(f"{medal} {label}  \n`{peso} m` (+{extra} m)")

# --- Construcción del figura con annotations ---
img = Image.open('mapa_ua.jpg')

# Preparar annotations de distancias
annotations = []
for u, v, data in G.edges(data=True):
    x0, y0 = posiciones[u]
    x1, y1 = posiciones[v]
    mx = (x0 + x1) / 2
    my = ((1000 - y0) + (1000 - y1)) / 2
    annotations.append(dict(
        x=mx, y=my,
        text=f"<b>{data['weight']}m</b>",
        showarrow=False,
        font=dict(color='black', size=10),
        bgcolor='rgba(255,255,255,0.85)',
        bordercolor='#888',
        borderwidth=1,
        borderpad=3,
        xref='x', yref='y'
    ))

ruta = st.session_state.ruta
ruta_set = set()
if ruta:
    for i in range(len(ruta)-1):
        a, b = ruta[i], ruta[i+1]
        ruta_set.add((a, b))
        ruta_set.add((b, a))

traces = []

# Imagen de fondo
fig = go.Figure()
fig.add_layout_image(dict(
    source=img, xref="x", yref="y",
    x=0, y=1000, sizex=1000, sizey=1000,
    sizing="stretch", layer="below"
))

# Aristas negras
for u, v in G.edges():
    x0, y0 = posiciones[u]
    x1, y1 = posiciones[v]
    fig.add_trace(go.Scatter(
        x=[x0, x1, None], y=[1000-y0, 1000-y1, None],
        mode='lines',
        line=dict(color='black', width=2, dash='dot'),
        showlegend=False, hoverinfo='skip',
        name=''
    ))

# Árbol de expansión mínima (verde)
if st.session_state.arbol_aristas:
    for u, v in st.session_state.arbol_aristas:
        x0, y0 = posiciones[u]
        x1, y1 = posiciones[v]
        fig.add_trace(go.Scatter(
            x=[x0, x1, None], y=[1000-y0, 1000-y1, None],
            mode='lines',
            line=dict(color='green', width=6),
            showlegend=False, hoverinfo='skip',
            name=''
        ))

# Ruta roja
if ruta:
    for i in range(len(ruta)-1):
        x0, y0 = posiciones[ruta[i]]
        x1, y1 = posiciones[ruta[i+1]]
        fig.add_trace(go.Scatter(
            x=[x0, x1, None], y=[1000-y0, 1000-y1, None],
            mode='lines',
            line=dict(color='red', width=5),
            showlegend=False, hoverinfo='skip',
            name=''
        ))

# Nodos
x_n = [p[0] for p in posiciones.values()]
y_n = [1000-p[1] for p in posiciones.values()]
fig.add_trace(go.Scatter(
    x=x_n, y=y_n,
    mode='markers+text',
    text=list(posiciones.keys()),
    textposition='middle center',
    marker=dict(size=22, color='white', line=dict(width=2, color='black')),
    textfont=dict(color='black', size=13),
    showlegend=False, hoverinfo='skip',
    name=''
))

fig.update_xaxes(visible=False, range=[0, 1000])
fig.update_yaxes(visible=False, range=[0, 1000], scaleanchor="x")
fig.update_layout(
    plot_bgcolor='white',
    paper_bgcolor='white',
    margin=dict(l=0, r=0, t=0, b=0),
    showlegend=False,
    annotations=annotations
)

col2.plotly_chart(fig, use_container_width=True)