
import streamlit as st
import plotly.graph_objects as go
import requests
import datetime
import io
import re
import unicodedata
import zipfile
import sys
import subprocess
from pathlib import Path
from pypdf import PdfWriter
import streamlit.components.v1 as components
from src.raa_core import scrape_and_merge
from src.raa_client import QuotaManager
from src.clients.clients import DEPARTMENT_URLS
from run import run as raa_run

st.set_page_config(page_title="Test Streamlit", page_icon="🚀", layout="wide")

PROJECT_DIR = Path(__file__).parent
RAA_ROOT = PROJECT_DIR / "raa_pdfs"
IMPORT_MAX_DOCS = 3
IMPORT_TIMEOUT_S = 600

def execute_import(dept, month, log_callback=None):
    try:
        # Appel direct à la fonction run de run.py
        merged_path = raa_run(
            department=dept,
            year=str(month.year),
            month=f"{month.month:02d}",
            dest_folder=str(RAA_ROOT),
            max_docs=IMPORT_MAX_DOCS,
            output_func=log_callback if log_callback else print
        )
        return True, f"Import terminé. Fusionné : {merged_path}"
    except Exception as e:
        return False, str(e)

def request_import(dept, month):
    st.session_state.pending_imports = [(dept, month)]
    st.session_state.import_running = True

def request_import_all(selected_depts, current_month):
    missing = []
    for dept in selected_depts:
        indiv, merged, _ = get_raa_files(dept, current_month)
        if not indiv and not merged:
            missing.append((dept, current_month))
    
    if missing:
        st.session_state.pending_imports = missing
        st.session_state.import_running = True

MONTHS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",

              "août", "septembre", "octobre", "novembre", "décembre"]

def _norm(s):
    if s is None: return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def _natural_key(name):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", _norm(name))]

def _find_subdir(parent, wanted):
    if not parent.exists() or not parent.is_dir():
        return None
    wanted_norm = _norm(wanted)
    for item in parent.iterdir():
        if item.is_dir() and _norm(item.name) == wanted_norm:
            return item
    return None

@st.cache_data(ttl=60)
def dept_folders():
    if not RAA_ROOT.exists():
        return {}
    return {_norm(d.name): str(d) for d in RAA_ROOT.iterdir() if d.is_dir()}

def get_raa_files(dept_name, month):
    # month is a datetime.date object
    d_norm = _norm(dept_name)
    folders = dept_folders()
    if d_norm not in folders:
        return ((), None, False)
    
    dept_path = Path(folders[d_norm])
    year_str = str(month.year)
    month_name_fr = MONTHS_FR[month.month - 1]
    
    # 1. Individuels : <dept>/<année>/<mois>/*.pdf
    year_dir = _find_subdir(dept_path, year_str)
    month_dir = _find_subdir(year_dir, month_name_fr) if year_dir else None
    
    individual = ()
    if month_dir:
        pdfs = list(month_dir.glob("*.pdf"))
        individual = tuple(sorted([(str(p), p.stat().st_mtime) for p in pdfs], key=lambda x: _natural_key(x[0])))
    
    # 2. Fusionnés : racine du dept, contient 'fusionne' et '<mois>-<année>'
    merged = None
    is_partial = False
    
    # We look for all pdfs in dept root
    merged_candidates = list(dept_path.glob("*.pdf"))
    
    # Normalization tokens
    month_token = _norm(month_name_fr)
    year_token = _norm(year_str)
    
    # Sort by mtime descending to get the most recent
    merged_candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    # Priority: Complet > Partiel
    best_merged = None
    best_mtime = -1
    best_is_partial = False

    for p in merged_candidates:
        p_norm = _norm(p.name)
        if "fusionne" in p_norm and month_token in p_norm and year_token in p_norm:
            partial = "partiel" in p_norm
            mtime = p.stat().st_mtime
            
            if best_merged is None:
                best_merged = (str(p), mtime)
                best_is_partial = partial
            elif partial and not best_is_partial:
                # Current is partial, best is complete. Keep best.
                continue
            elif not partial and best_is_partial:
                # Current is complete, best was partial. Current wins.
                best_merged = (str(p), mtime)
                best_is_partial = partial
            elif mtime > best_mtime:
                # Same type, take newest
                best_merged = (str(p), mtime)
                best_is_partial = partial
                
    return individual, best_merged, best_is_partial

@st.cache_data
def read_file(path, mtime):
    with open(path, "rb") as f:
        return f.read()

@st.cache_data
def merged_pdf(individual):
    # individual is tuple of (path, mtime)
    writer = PdfWriter()
    for path, _ in individual:
        writer.append(path)
    
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()

@st.cache_data
def zip_merged(by_dept):
    # by_dept = ((arcname, merged_bytes, individual_tuple), ...)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for arcname, merged, individual in by_dept:
            if merged:
                z.writestr(arcname, merged)
            elif individual:
                z.writestr(arcname, merged_pdf(individual))
    return buf.getvalue()

@st.cache_data
def zip_individual(entries):
    # entries = ((arcname, path_str), ...)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for arcname, path in entries:
            z.write(path, arcname)
    return buf.getvalue()

st.title("🗺️  Carte des départements")

# Centre (lon, lat) de chaque case DOM, dans le vide à l'ouest de l'hexagone
DOM_POSITIONS = {
    "971": (-7.5, 50.0),  # Guadeloupe
    "972": (-7.5, 48.0),  # Martinique
    "973": (-7.5, 46.0),  # Guyane
    "974": (-7.5, 44.0),  # La Réunion
    "976": (-7.5, 42.0),  # Mayotte
}
BOX_SIZE = 1.6  # taille d'une case, en degrés


def _rings(geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        yield from poly


def relocate_dom(geojson):
    for feature in geojson["features"]:
        target = DOM_POSITIONS.get(feature["properties"]["code"])
        if target is None:
            continue
        rings = list(_rings(feature["geometry"]))
        lons = [p[0] for r in rings for p in r]
        lats = [p[1] for r in rings for p in r]
        cx, cy = (min(lons) + max(lons)) / 2, (min(lats) + max(lats)) / 2
        scale = BOX_SIZE / max(max(lons) - min(lons), max(lats) - min(lats))
        for ring in rings:
            for p in ring:
                p[0] = target[0] + (p[0] - cx) * scale
                p[1] = target[1] + (p[1] - cy) * scale
    return geojson


@st.cache_data
def load_geojson():
    url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-avec-outre-mer.geojson"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return relocate_dom(response.json())
    except Exception as e:
        st.error(f"Erreur lors du chargement du GeoJSON: {e}")
    return {"type": "FeatureCollection", "features": []}


geojson = load_geojson()
all_depts = sorted(f["properties"]["nom"] for f in geojson["features"])
dept_codes = {f["properties"]["nom"]: f["properties"]["code"] for f in geojson["features"]}

# Une seule source de vérité : la clé du selectbox
MONTHS = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet",
            "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
today = datetime.date.today()
YEARS = list(range(today.year, 1999, -1))  # plus récent en premier


if "dept_selector" not in st.session_state:
    st.session_state.dept_selector = []
if "map_version" not in st.session_state:
    st.session_state.map_version = 0

def on_map_select():
    key = f"map_{st.session_state.map_version}"
    if key not in st.session_state:
        return
    points = st.session_state[key].selection.points
    clicked = [all_depts[p["point_index"]] for p in points if p["curve_number"] == 0]
    if clicked:
        current = list(st.session_state.dept_selector)
        dept = clicked[-1]
        # Uniquement si le département est implémenté
        if dept in DEPARTMENT_URLS:
            if dept in current:
                current.remove(dept)
            else:
                current.append(dept)
        st.session_state.dept_selector = current
    st.session_state.map_version += 1  # repart d'une sélection Plotly propre

def on_multiselect_change():
    # Nouvelle clé de graphique => widget neuf, la carte suit exactement
    st.session_state.map_version += 1


col_map, col_month = st.columns([3, 1], gap="medium")

with col_map:
    selected_depts = st.multiselect(
        "Quels départements voulez-vous voir ?",
        sorted(list(DEPARTMENT_URLS.keys())),
        key="dept_selector",
        on_change=on_multiselect_change,
        placeholder="Clic sur la carte, Shift+clic pour en ajouter",
    )


with col_month:
    col_m, col_y = st.columns([3, 2])
    with col_m:
        month_name = st.selectbox("🗓️ Mois", MONTHS, key="month_selector")
    with col_y:
        year = st.selectbox("Année", YEARS, key="year_selector")
    current_month = datetime.date(year, MONTHS.index(month_name) + 1, 1)

common = {
    "geojson": geojson,
    "featureidkey": "properties.nom",
    "showscale": False,
    "marker_line_color": "black",
    "marker_line_width": 0.3,
    "hoverinfo": "location",
    "selected": {"marker": {"opacity": 1}},
    "unselected": {"marker": {"opacity": 1}},  # évite l'effet "grisé"
}

fig = go.Figure()
selected_set = set(selected_depts)
# z = 0: Non implémenté, 1: Implémenté non sélectionné, 2: Implémenté sélectionné
z_values = []
for d in all_depts:
    if d not in DEPARTMENT_URLS:
        z_values.append(0)
    elif d in selected_set:
        z_values.append(2)
    else:
        z_values.append(1)

fig.add_trace(go.Choropleth(
    locations=all_depts,
    z=z_values,
    zmin=0,
    zmax=2,
    colorscale=[
        [0.0, "#444444"], [0.3, "#444444"], 
        [0.3, "#EEEEEE"], [0.7, "#EEEEEE"], 
        [0.7, "#FF4B4B"], [1.0, "#FF4B4B"]
    ],
    # Plotly repart de la sélection Python => Shift+clic ajoute aux depts déjà choisis
    selectedpoints=[i for i, d in enumerate(all_depts) if d in selected_set],
    **common,
))

# Cadres autour des cases DOM
half = BOX_SIZE / 2 + 0.15
box_lons, box_lats = [], []
for lon, lat in DOM_POSITIONS.values():
    box_lons += [lon - half, lon + half, lon + half, lon - half, lon - half, None]
    box_lats += [lat - half, lat - half, lat + half, lat + half, lat - half, None]
fig.add_trace(go.Scattergeo(
    lon=box_lons, lat=box_lats, mode="lines",
    line={"color": "#999999", "width": 1},
    hoverinfo="skip", showlegend=False,
))

fig.update_geos(
    projection_type="mercator",
    visible=False,
    lonaxis_range=[-9, 10],
    lataxis_range=[40.5, 51.5],
)
fig.update_layout(
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    clickmode="event+select",
    height=450,
)

with col_map:
    st.plotly_chart(fig, key=f"map_{st.session_state.map_version}", on_select=on_map_select,
                    selection_mode="points", use_container_width=True)

col_head, col_q = st.columns([4, 1])
with col_head:
    st.subheader(f"Départements sélectionnés ({len(selected_depts)}) — {month_name} {year}")
with col_q:
    used, remaining, time_left = QuotaManager.get_quota_status()
    st.markdown(f"📦 **Quota d'import:** `{used}/{QuotaManager.LIMIT}`")
    
    if time_left > 0:
        # Timer et Bouton Reset temps réel via un composant JS
        start_time = QuotaManager.get_start_time()
        reset_timestamp = start_time + QuotaManager.WINDOW
        
        timer_html = f"""
        <div style="font-family: sans-serif; font-size: 12px; color: #666; margin-top: -10px; display: flex; align-items: center; gap: 8px;">
            <span>Reset dans <span id="timer">--:--</span></span>
            <button id="refresh-btn" style="display: none; cursor: pointer; background: #f0f2f6; border: 1px solid #ccc; border-radius: 4px; padding: 1px 6px; font-size: 11px;" onclick="window.parent.location.reload()">🔄 Actualiser</button>
        </div>
        <script>
            const resetTime = {reset_timestamp} * 1000;
            function updateTimer() {{
                const now = new Date().getTime();
                const diff = resetTime - now;
                const timerEl = document.getElementById('timer');
                const btnEl = document.getElementById('refresh-btn');
                if (diff <= 0) {{
                    timerEl.innerHTML = "Reset !";
                    btnEl.style.display = "inline-block";
                    return;
                }}
                const mins = Math.floor((diff / (1000 * 60)));
                const secs = Math.floor((diff % (1000 * 60)) / 1000);
                timerEl.innerHTML = mins + "m " + (secs < 10 ? "0" : "") + secs + "s";
                btnEl.style.display = "none";
            }}
            setInterval(updateTimer, 1000);
            updateTimer();
        </script>
        """
        components.html(timer_html, height=30)


status_slot = st.container()
import_result = st.session_state.pop("import_result", None)
if import_result:
    dept_done, ok, output = import_result
    with status_slot:
        if ok:
            st.success(f"Import des RAA de {dept_done} terminé.")
        else:
            st.error(f"Échec de l'import des RAA de {dept_done}.")
        with st.expander("Sortie du processus d'importation"):
            st.code(output)

if not selected_depts:
    st.info("Aucun département sélectionné.")
else:
    # Tri par code INSEE
    sorted_selected = sorted(selected_depts, key=lambda d: dept_codes.get(d, "999"))
    
    # 1. Pré-calcul des données pour les ZIP et la visibilité
    has_any_files = False
    has_individuals = False
    has_missing_imports = False
    zip_merged_data = [] # (arcname, merged_bytes, individual)
    zip_individual_data = [] # (arcname, path)

    for dept in sorted_selected:
        code = dept_codes.get(dept, "??")
        indiv, merged, partial = get_raa_files(dept, current_month)
        
        if not indiv and not merged:
            has_missing_imports = True
            continue
        
        has_any_files = True
        
        # Déterminer le fusionné pour le ZIP
        merged_bytes = None
        merged_filename = ""
        if merged:
            merged_path, mtime = merged
            merged_bytes = read_file(merged_path, mtime)
            merged_filename = Path(merged_path).name
        elif indiv:
            merged_bytes = merged_pdf(indiv)
            merged_filename = f"RAA_fusionne_{month_name}_{year}_{dept}.pdf"
        
        if merged_bytes:
            zip_merged_data.append((merged_filename, merged_bytes, indiv))
            
        for path, _ in indiv:
            zip_individual_data.append((f"{dept}/{Path(path).name}", path))
            has_individuals = True

    # 2. Affichage des boutons d'action en haut
    if has_any_files or has_missing_imports:
        used, _, _ = QuotaManager.get_quota_status()
        quota_reached = used >= QuotaManager.LIMIT
        
        widgets = []
        if has_any_files:
            widgets.append("merged")
        if has_individuals:
            widgets.append("indiv")
        if has_missing_imports:
            widgets.append("import")
        
        if widgets:
            cols = st.columns(len(widgets))
            for i, w_type in enumerate(widgets):
                with cols[i]:
                    if w_type == "merged":
                        st.download_button(
                            "🗂️  ZIP : un PDF fusionné par département", 
                            zip_merged(tuple(zip_merged_data)), 
                            file_name=f"RAA_fusionnes_{current_month.strftime('%Y-%m')}.zip", 
                            key="zip_merged", on_click="ignore"
                        )
                    elif w_type == "indiv":
                        st.download_button(
                            "📦 ZIP : tous les RAA individuels", 
                            zip_individual(tuple(zip_individual_data)), 
                            file_name=f"RAA_{current_month.strftime('%Y-%m')}.zip", 
                            key="zip_individual", on_click="ignore"
                        )
                    elif w_type == "import":
                        st.button(
                            "📥 Importer : tous les RAA manquants", 
                            key="import_all_btn", 
                            on_click=request_import_all, 
                            args=(selected_depts, current_month),
                            disabled=st.session_state.get("import_running", False) or quota_reached
                        )
        st.divider()

    # 3. Affichage de la liste détaillée
    empty_depts = []
    for dept in sorted_selected:
        code = dept_codes.get(dept, "??")
        indiv, merged, partial = get_raa_files(dept, current_month)
        
        if not indiv and not merged:
            empty_depts.append((dept, code))
            col_warn, col_btn = st.columns([0.8, 0.2])
            with col_warn:
                st.caption(f"**{code}** — {dept} · aucun RAA pour ce mois.")
            with col_btn:
                used, _, _ = QuotaManager.get_quota_status()
                quota_reached = used >= QuotaManager.LIMIT
                st.button(
                    "Importer", key=f"import_{code}",
                    on_click=request_import, args=(dept, current_month),
                    disabled=st.session_state.get("import_running", False) or quota_reached,
                )
                continue

        
        n_indiv = len(indiv)
        label = f"**{code}** — {dept} · {n_indiv} RAA"
        if partial:
            label += " · ⚠️  fusion partielle"
        
        with st.expander(label):
            # Bouton Fusionner (si indiv existents mais pas de merged complet)
            if indiv and (not merged or partial):
                if st.button("Fusionner", key=f"merge_{code}", disabled=partial):
                    with st.status(f"Fusion des RAA de {dept}...", expanded=True) as status:
                        prog = st.progress(0)
                        def cb(done, total, msg):
                            prog.progress(done / total if total > 0 else 0)
                            st.write(msg)
                        try:
                            scrape_and_merge(
                                department=dept,
                                year=str(current_month.year),
                                month=f"{current_month.month:02d}",
                                dest_folder=RAA_ROOT,
                                progress_cb=cb
                            )
                            status.update(label="Fusion terminée !", state="complete")
                            dept_folders.clear()
                            st.rerun()
                        except Exception as e:
                            status.update(label="Erreur de fusion", state="error")
                            st.error(str(e))


            # Bouton Fusionné existant
            merged_bytes = None
            merged_filename = ""
            if merged:
                merged_path, mtime = merged
                merged_bytes = read_file(merged_path, mtime)
                merged_filename = Path(merged_path).name
            elif indiv:
                merged_bytes = merged_pdf(indiv)
                merged_filename = f"RAA_fusionne_{month_name}_{year}_{dept}.pdf"
            
            if merged_bytes:
                btn_label = "📑 Tous les RAA du département (PDF fusionné)"
                if partial: btn_label += " — partiel"
                st.download_button(btn_label, merged_bytes, file_name=merged_filename, 
                                    key=f"merged_{code}", on_click="ignore")
            
            for path, mtime in indiv:
                st.download_button(f"📄 {Path(path).name}", read_file(path, mtime), 
                                   file_name=Path(path).name, key=f"file_{path}", on_click="ignore")

pending = st.session_state.get("pending_imports")
if pending:
    with status_slot:
        with st.status("Importation des RAA manquants...", expanded=True) as batch_status:
            # Zone pour les logs en temps réel
            log_display = st.empty()
            logs = []

            def log_callback(line):
                logs.append(line)
                # On affiche les 15 dernières lignes pour ne pas saturer l'écran
                log_display.code("".join(logs[-15:]))

            results = []
            for dept, month in pending:
                st.write(f"⏳ Import de {dept}...")
                ok, output = execute_import(dept, month, log_callback=log_callback)
                if ok:
                    st.write(f"✅ {dept} terminé")
                else:
                    st.write(f"❌ {dept} échoué")
                results.append((dept, ok, output))
            
            batch_status.update(label="Importations terminées", state="complete")
    
    st.session_state.import_result = results[-1] if results else None
    st.session_state.pending_imports = None
    st.session_state.import_running = False
    dept_folders.clear()
    st.rerun()





