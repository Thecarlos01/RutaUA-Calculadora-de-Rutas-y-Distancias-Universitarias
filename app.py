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

# --- Estado de sesión ---
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
if 'bloqueadas' not in st.session_state:
    st.session_state.bloqueadas = set()          # set of tuples (u, v) ordenados
if 'ultimo_click_id' not in st.session_state:
    st.session_state.ultimo_click_id = None


def calcular_peso_ruta(ruta, grafo=None):
    g = grafo if grafo is not None else G
    return sum(g[ruta[i]][ruta[i+1]]['weight'] for i in range(len(ruta)-1))


def obtener_grafo_activo():
    """Copia del grafo sin las conexiones bloqueadas por el usuario."""
    Gc = G.copy()
    for (u, v) in st.session_state.bloqueadas:
        if Gc.has_edge(u, v):
            Gc.remove_edge(u, v)
    return Gc


def limpiar_resultados():
    """Limpia rutas/árboles calculados, ya que dejan de ser válidos al bloquear/desbloquear."""
    st.session_state.ruta = []
    st.session_state.distancia_total = 0
    st.session_state.todas_rutas = []
    st.session_state.arbol_aristas = []
    st.session_state.arbol_peso_total = 0
    st.session_state.arbol_algoritmo = ''
    st.session_state.todos_arboles = []


col1, col2 = st.columns([1, 3])
with col1:
    origen = st.selectbox("Punto de partida:", sorted(posiciones.keys()))
    destino = st.selectbox("Destino:", sorted(posiciones.keys()))

    st.markdown("---")

    # Botón 1: ruta óptima directa
    if st.button("🗺️ Calcular Ruta"):
        st.session_state.todas_rutas = []
        Gc = obtener_grafo_activo()
        try:
            st.session_state.ruta = nx.shortest_path(Gc, source=origen, target=destino, weight='weight')
            st.session_state.distancia_total = calcular_peso_ruta(st.session_state.ruta, Gc)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            st.session_state.ruta = []
            st.error("No hay camino disponible con las conexiones bloqueadas actuales")

    # Botón 2: comparar todas las rutas posibles
    if st.button("⚡ Mostrar Ruta más Corta"):
        Gc = obtener_grafo_activo()
        try:
            todos = list(nx.all_simple_paths(Gc, source=origen, target=destino))
            if not todos:
                st.error("No hay camino disponible con las conexiones bloqueadas actuales")
                st.session_state.todas_rutas = []
            else:
                rutas_con_peso = sorted(
                    [(r, calcular_peso_ruta(r, Gc)) for r in todos],
                    key=lambda x: x[1]
                )
                st.session_state.todas_rutas = rutas_con_peso
                st.session_state.ruta = rutas_con_peso[0][0]
                st.session_state.distancia_total = rutas_con_peso[0][1]
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            st.session_state.todas_rutas = []
            st.error("No hay camino disponible con las conexiones bloqueadas actuales")

    st.markdown("---")

    # Botón 3: árbol de expansión mínimo con Prim
    if st.button("🌳 Árbol de Expansión Mínimo Prim"):
        st.session_state.todos_arboles = []
        Gc = obtener_grafo_activo()
        try:
            arbol = nx.minimum_spanning_tree(Gc, weight='weight', algorithm='prim')
            if not nx.is_connected(Gc) or not arbol.edges():
                st.error("No hay árbol de expansión posible con las conexiones bloqueadas actuales")
                st.session_state.arbol_aristas = []
            else:
                st.session_state.arbol_aristas = list(arbol.edges())
                st.session_state.arbol_peso_total = sum(
                    data['weight'] for _, _, data in arbol.edges(data=True)
                )
                st.session_state.arbol_algoritmo = 'Prim'
        except Exception:
            st.session_state.arbol_aristas = []
            st.error("No hay árbol de expansión posible con las conexiones bloqueadas actuales")

    # Botón 4: árbol de expansión mínimo con Kruskal
    if st.button("🌳 Árbol de Expansión Mínimo Kruskal"):
        st.session_state.todos_arboles = []
        Gc = obtener_grafo_activo()
        try:
            arbol = nx.minimum_spanning_tree(Gc, weight='weight', algorithm='kruskal')
            if not nx.is_connected(Gc) or not arbol.edges():
                st.error("No hay árbol de expansión posible con las conexiones bloqueadas actuales")
                st.session_state.arbol_aristas = []
            else:
                st.session_state.arbol_aristas = list(arbol.edges())
                st.session_state.arbol_peso_total = sum(
                    data['weight'] for _, _, data in arbol.edges(data=True)
                )
                st.session_state.arbol_algoritmo = 'Kruskal'
        except Exception:
            st.session_state.arbol_aristas = []
            st.error("No hay árbol de expansión posible con las conexiones bloqueadas actuales")

    # Botón 5: comparar todos los árboles de expansión posibles
    if st.button("📊 Comparar Árboles de Expansión"):
        st.session_state.todos_arboles = []
        Gc = obtener_grafo_activo()
        try:
            n = Gc.number_of_nodes()
            edges = list(Gc.edges())
            arboles_con_peso = []
            for combo in itertools.combinations(edges, n - 1):
                H = nx.Graph()
                H.add_nodes_from(Gc.nodes())
                H.add_edges_from(combo)
                if nx.is_connected(H):
                    peso = sum(Gc[u][v]['weight'] for u, v in combo)
                    arboles_con_peso.append((combo, peso))

            if not arboles_con_peso:
                st.error("No hay árbol de expansión posible con las conexiones bloqueadas actuales")
            else:
                arboles_con_peso.sort(key=lambda x: x[1])
                st.session_state.todos_arboles = arboles_con_peso
                st.session_state.arbol_aristas = list(arboles_con_peso[0][0])
                st.session_state.arbol_peso_total = arboles_con_peso[0][1]
                st.session_state.arbol_algoritmo = 'Comparación'
        except Exception:
            st.session_state.todos_arboles = []
            st.error("No hay árbol de expansión posible con las conexiones bloqueadas actuales")

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
        if st.button("❌ Ocultar ruta"):
            st.session_state.ruta = []
            st.session_state.distancia_total = 0
            st.session_state.todas_rutas = []

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

    # --- Conexiones bloqueadas ---
    st.markdown("---")
    st.markdown("### 🚧 Conexiones bloqueadas")
    st.caption("Haz clic en el círculo sobre una conexión del mapa para bloquearla o desbloquearla.")
    if st.session_state.bloqueadas:
        for (u, v) in sorted(st.session_state.bloqueadas):
            st.warning(f"🚫 {u}-{v}")
        if st.button("🔓 Desbloquear todas las conexiones"):
            st.session_state.bloqueadas = set()
            limpiar_resultados()
            st.rerun()
    else:
        st.caption("No hay conexiones bloqueadas.")

# --- Construcción de la figura con annotations ---
img = Image.open('mapa_ua.jpg')

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

fig = go.Figure()
fig.add_layout_image(dict(
    source=img, xref="x", yref="y",
    x=0, y=1000, sizex=1000, sizey=1000,
    sizing="stretch", layer="below"
))

# Aristas: negras si están libres, grises/atenuadas si están bloqueadas
for u, v in G.edges():
    x0, y0 = posiciones[u]
    x1, y1 = posiciones[v]
    arista = tuple(sorted((u, v)))
    bloqueada = arista in st.session_state.bloqueadas
    fig.add_trace(go.Scatter(
        x=[x0, x1, None], y=[1000-y0, 1000-y1, None],
        mode='lines',
        line=dict(
            color='#bbbbbb' if bloqueada else 'black',
            width=2,
            dash='dot'
        ),
        opacity=0.5 if bloqueada else 1.0,
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

# Puntos clicables sobre el punto medio de cada conexión (bloquear/desbloquear)
click_x, click_y, click_color, click_text, click_customdata = [], [], [], [], []
for u, v, data in G.edges(data=True):
    x0, y0 = posiciones[u]
    x1, y1 = posiciones[v]
    mx = (x0 + x1) / 2
    my = 1000 - ((y0 + y1) / 2)
    arista = tuple(sorted((u, v)))
    bloqueada = arista in st.session_state.bloqueadas
    click_x.append(mx)
    click_y.append(my)
    click_color.append('#e74c3c' if bloqueada else '#2ecc71')
    click_text.append(f"{'🔓 Desbloquear' if bloqueada else '🔒 Bloquear'} {u}-{v} ({data['weight']}m)")
    click_customdata.append([u, v])

fig.add_trace(go.Scatter(
    x=click_x, y=click_y,
    mode='markers',
    marker=dict(size=16, color=click_color, symbol='circle',
                line=dict(width=2, color='white')),
    customdata=click_customdata,
    hovertext=click_text,
    hoverinfo='text',
    showlegend=False,
    name='conexiones'
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
    annotations=annotations,
    clickmode='event+select'
)

evento = col2.plotly_chart(
    fig,
    use_container_width=True,
    key="mapa_click",
    on_select="rerun",
    selection_mode="points"
)

# Procesar clic sobre una conexión (marcador verde/rojo)
if evento and evento.get("selection", {}).get("points"):
    punto = evento["selection"]["points"][0]
    identificador = (punto.get("curve_number"), punto.get("point_index"))
    if identificador != st.session_state.ultimo_click_id:
        st.session_state.ultimo_click_id = identificador
        customdata = punto.get("customdata")
        if customdata and len(customdata) == 2:
            u, v = customdata[0], customdata[1]
            arista = tuple(sorted((u, v)))
            if arista in st.session_state.bloqueadas:
                st.session_state.bloqueadas.discard(arista)
            else:
                st.session_state.bloqueadas.add(arista)
            limpiar_resultados()
            st.rerun()
