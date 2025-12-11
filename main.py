import streamlit as st
import pandas as pd
import numpy as np

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Shipping Calculation Dashboard", layout="wide")

# ==========================================
# 1. DATABASE SETUP (DATA RIIL)
# ==========================================

# A. DATA KAPAL
data_kapal = {
    "Nama Kapal": ["AKA", "ASJ", "ASN", "BGI", "BKU", "BSA"],
    "ME_Cons_L_Day": [4050, 6800, 10500, 4500, 4500, 4500],
    "AE_Cons_L_Day": [500, 1100, 1080, 528, 528, 528],
    "DOC_OH": [66504323, 93106052, 93106052, 66504323, 66504323, 66504323]
}
df_kapal = pd.DataFrame(data_kapal)

# B. DATA BIAYA PELABUHAN
data_port = {
    "Port": ["MKS", "SMG", "JYP", "PNK", "SDA", "KDR", "BPN", "SBY", "JKT"],
    "Biaya": [27750000, 25500000, 34500000, 24000000, 23250000, 22500000, 26250000, 28500000, 31500000]
}
df_port = pd.DataFrame(data_port)

# C. DATA JARAK (MATRIX)
ports_order = ['MKS', 'SMG', 'JYP', 'PNK', 'SDA', 'KDR', 'BPN', 'SBY', 'JKT']
matrix_data = [
    [0, 1014.2, 2380.43, 1254.2, 560.81, 376.99, 527.74, 774.84, 1391.5],
    [1014.2, 0, 3390.75, 779.39, 1032.94, 1389, 954.59, 256.06, 402.91],
    [2380.43, 3390.75, 0, 3499.33, 2621.86, 2015.05, 2663.67, 3142.64, 3771.8],
    [1254.2, 779.39, 3499.33, 0, 877.58, 1540.65, 838.1, 884.67, 730.05],
    [560.81, 1032.94, 2621.86, 877.58, 0, 711.06, 79.83, 890.02, 1301.03],
    [376.99, 1389, 2015.05, 1540.65, 711.06, 0, 720.46, 1151.76, 1759.51],
    [527.74, 954.59, 2663.67, 838.1, 79.83, 720.46, 0, 810.25, 1229.52],
    [774.84, 256.06, 3142.64, 884.67, 890.02, 1151.76, 810.25, 0, 658.09],
    [1391.5, 402.91, 3771.8, 730.05, 1301.03, 1759.51, 1229.52, 658.09, 0]
]
df_matrix = pd.DataFrame(matrix_data, columns=ports_order, index=ports_order)
df_jarak_flat = df_matrix.stack().reset_index()
df_jarak_flat.columns = ['Asal', 'Tujuan', 'Jarak']


# D. DATA THC (FL & MT) 20'
data_thc = {
    "Port": ["BLW","BTM","PLM","PKB","SPT","BMS","BLC","BPN",
             "SDA","TRK","BRU","NNK","MKS","SBY","JKT","KBR"],
    "FL":   [1080024, 566500, 687500, 883589, 535568, 688800, 722267, 1035101,
             940500, 915215, 617375, 981747, 807904, 840215, 872500, 840215],
    "MT":   [503982, 381260, 515625, 577931, 377300, 490001, 403596, 716650,
             636900, 499934, 320100, 585935, 437250, 584200, 564400, 584200],
}
df_thc = pd.DataFrame(data_thc).set_index("Port")

# E. DATA DEFAULT TOS (INBOUND / OUTBOUND)
data_tos = {
    "Port":    ["BLW","BTM","PLM","PKB","SPT","BMS","BLC","BPN",
                "SDA","TRK","BRU","NNK","MKS","SBY","JKT","KBR"],
    "Inbound": ["PORT","CY ( FIOST )","CY ( FIOST )","PORT","PORT","PORT","PORT","PORT",
                "PORT","PORT","PORT","CY","PORT","PORT","PORT","PORT"],
    "Outbound":["PORT","CY ( FIOST )","CY ( FIOST )","PORT","PORT","PORT","PORT","PORT",
                "PORT","PORT","PORT","CY","PORT","PORT","PORT","PORT"],
}
df_tos = pd.DataFrame(data_tos).set_index("Port")

HUBS = {"SBY", "JKT"}  # rute hub-hub = THC 0

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def get_distance(port_a, port_b):
    res = df_jarak_flat[(df_jarak_flat["Asal"] == port_a) & (df_jarak_flat["Tujuan"] == port_b)]
    if not res.empty: return res.iloc[0]["Jarak"]
    return -1

def format_rupiah_compact(x: float) -> str:
    """Format rupiah: 6.000.000 -> 'Rp 6 JT', 5.000.000.000 -> 'Rp 5 M'."""
    sign = "-" if x < 0 else ""
    n = abs(x)

    if n >= 1_000_000_000_000:
        val = n / 1_000_000_000_000
        suffix = " T"
    elif n >= 1_000_000_000:
        val = n / 1_000_000_000
        suffix = " M"
    elif n >= 1_000_000:
        val = n / 1_000_000
        suffix = " JT"
    else:
        # kalau di bawah 1 juta, tampilkan full
        return f"Rp {x:,.0f}"

    return f"Rp {sign}{val:,.0f}{suffix}"

def calculate_operational_cost(ship_name, route_str, ship_speed):
    DAYS_PER_PORT = 1.0
    
    kapal = df_kapal[df_kapal["Nama Kapal"] == ship_name].iloc[0]
    me_cons, ae_cons, doc_fixed = kapal["ME_Cons_L_Day"], kapal["AE_Cons_L_Day"], kapal["DOC_OH"]

    route_clean = route_str.replace(" ", "").upper()
    ports = route_clean.split("-")
    if len(ports) < 2: return None, "Rute minimal 2 pelabuhan."

    total_dist, total_sailing = 0, 0
    for i in range(len(ports)-1):
        if ports[i] not in ports_order or ports[i+1] not in ports_order:
            return None, f"Port salah: {ports[i]} atau {ports[i+1]}"
        d = get_distance(ports[i], ports[i+1])
        if d < 0: return None, f"Jarak not found: {ports[i]}-{ports[i+1]}"
        total_dist += d
        total_sailing += (d / ship_speed) / 24

    total_port_days = len(ports) * DAYS_PER_PORT
    total_me = total_sailing * me_cons
    total_ae = (total_sailing + total_port_days) * ae_cons
    
    port_cost = 0
    for p in ports:
        port_cost += df_port[df_port["Port"] == p].iloc[0]["Biaya"]

    return {
        "Jarak": total_dist, "ME_L": total_me, "AE_L": total_ae,
        "Total_L": total_me + total_ae, "DOC": doc_fixed, "PortCost": port_cost,
        "TotalOps": doc_fixed + port_cost
    }, None

def generate_revenue_template(route_str):
    """
    Generate kombinasi OD berdasarkan urutan rute.
    Contoh: JKT-SBY-MKS-SBY-JKT
    -> JKT-MKS, SBY-MKS, JKT-SBY, MKS-JKT, MKS-SBY, SBY-JKT
    - Hanya pasangan i < j (arah mengikuti pergerakan kapal)
    - Skip asal = tujuan
    - Skip duplikat (misal JKT-SBY muncul lebih dari sekali di rute)
    """
    ports = route_str.replace(" ", "").upper().split("-")
    if len(ports) < 2:
        return pd.DataFrame()

    seen_pairs = set()
    rows = []

    for i in range(len(ports)):
        for j in range(i + 1, len(ports)):
            asal = ports[i]
            tujuan = ports[j]

            # Lewati kalau sama (JKT-JKT, SBY-SBY, dst.)
            if asal == tujuan:
                continue

            key = (asal, tujuan)
            if key in seen_pairs:
                continue  # hindari duplikat

            seen_pairs.add(key)
            rows.append({
                "Kombinasi": f"{asal}-{tujuan}",
                "Port Asal": asal,          # THC OUTBOUND
                "Port Tujuan": tujuan,      # THC INBOUND
                "Jumlah Box": 0,
                "Harga/TEU (Rp)": 0,
                "Total Revenue (Rp)": 0
            })

    return pd.DataFrame(rows)


# --- CALLBACK UNTUK AUTO-CALCULATE REVENUE ---
def recalculate_revenue():
    """Fungsi ini dipanggil otomatis SAAT user mengedit tabel, SEBELUM halaman reload."""
    # 1. Ambil perubahan (delta) dari editor
    updates = st.session_state["editor_revenue"]
    
    # 2. Terapkan perubahan ke DataFrame utama di session_state
    for row_idx, col_dict in updates["edited_rows"].items():
        for col_name, new_val in col_dict.items():  
            st.session_state.df_revenue.at[int(row_idx), col_name] = new_val
            
    # 3. Hitung Rumus Perkalian (Vectorized)
    st.session_state.df_revenue["Total Revenue (Rp)"] = (
        st.session_state.df_revenue["Jumlah Box"] * st.session_state.df_revenue["Harga/TEU (Rp)"]
    )

def get_thc_rate(port: str, jenis: str, aksi: str) -> float:
    """
    port  : kode pelabuhan (SBY, JKT, MKS, ...)
    jenis : 'FL' atau 'MT'
    aksi  : 'L' (THL / loading) atau 'D' (THD / discharge)

    Aturan:
      - FULL (jenis='FL'):
            jika default TOS = PORT -> rate = 0
            jika CY / CY(FIOST)    -> pakai df_thc
      - EMPTY (jenis='MT'):
            TOS tidak menghapus biaya -> selalu pakai df_thc
    """
    try:
        dir_col = "Outbound" if aksi == "L" else "Inbound"
        tos = df_tos.loc[port, dir_col]
    except KeyError:
        return 0.0

    # FULL: kalau TOS = PORT, gratis (0)
    if jenis == "FL" and tos == "PORT":
        return 0.0

    # Selain itu (FULL CY / CY(FIOST), dan semua EMPTY/MT)
    try:
        return float(df_thc.loc[port, jenis])
    except KeyError:
        return 0.0
from collections import defaultdict

def find_first_leg_index(route_ports, asal, tujuan):
    """
    Cari posisi (index tujuan) pertama kali rute melewati asal->tujuan
    berdasarkan urutan port di input_route.
    Return: index tujuan (int) atau None jika tidak pernah terjadi.
    """
    n = len(route_ports)
    for i in range(n - 1):
        for j in range(i + 1, n):
            if route_ports[i] == asal and route_ports[j] == tujuan:
                return j  # pakai index tujuan sebagai 'waktu sampai'
    return None


from collections import defaultdict

def compute_empty_flows(df_revenue: pd.DataFrame, route_str: str):
    """
    Hitung aliran container kosong per leg (asal, tujuan) berdasarkan:
    - go = leg yang muncul LEBIH AWAL di rute
    - return = leg yang muncul LEBIH AKHIR di rute
    Q_empty(return) = max(Q_go - Q_return, 0)
    Q_empty(go)     = 0
    """
    route_ports = route_str.replace(" ", "").upper().split("-")

    # volume full per arah
    flows = {}
    unordered_pairs = set()

    for _, row in df_revenue.iterrows():
        asal = str(row["Port Asal"])
        tujuan = str(row["Port Tujuan"])
        if asal == tujuan:
            continue
        q = float(row["Jumlah Box"])
        flows[(asal, tujuan)] = q
        unordered_pairs.add(frozenset((asal, tujuan)))

    empty_flow = defaultdict(float)

    for pair in unordered_pairs:
        a, b = tuple(pair)
        q_ab = flows.get((a, b), 0.0)
        q_ba = flows.get((b, a), 0.0)

        # kalau salah satu arah tidak ada di tabel => tidak ada balikan => no empty
        if q_ab == 0.0 or q_ba == 0.0:
            continue

        pos_ab = find_first_leg_index(route_ports, a, b)
        pos_ba = find_first_leg_index(route_ports, b, a)

        # kalau salah satu tidak pernah muncul di rute => skip empty
        if pos_ab is None or pos_ba is None:
            continue

        # tentukan siapa "go" dan siapa "return"
        if pos_ab < pos_ba:
            go_dir = (a, b)
            ret_dir = (b, a)
            q_go, q_ret = q_ab, q_ba
        else:
            go_dir = (b, a)
            ret_dir = (a, b)
            q_go, q_ret = q_ba, q_ab

        q_empty = max(q_go - q_ret, 0.0)   # kalau negatif -> 0
        if q_empty > 0:
            empty_flow[ret_dir] = q_empty

    return empty_flow


def calculate_total_thc(df_revenue: pd.DataFrame, route_str: str):
    """
    Hitung total THC:
      - THC FULL  = (THL_FL(asal) + THD_FL(tujuan)) * Q_full
      - THC EMPTY = (THL_MT(asal) + THD_MT(tujuan)) * Q_empty
    Q_empty hanya muncul di LEG BALIKAN (lihat compute_empty_flows).
    Rute hub-hub (SBY<->JKT) -> THC = 0.
    """
    empty_flow = compute_empty_flows(df_revenue, route_str)
    total = 0.0
    detail_rows = []

    for _, row in df_revenue.iterrows():
        asal = str(row["Port Asal"])
        tujuan = str(row["Port Tujuan"])
        q_full = float(row["Jumlah Box"])

        # hub-hub: semua 0
        if asal in HUBS and tujuan in HUBS:
            detail_rows.append([asal, tujuan, q_full, 0.0, 0.0])
            continue

        # THC FULL (FL)
        rate_thl_fl = get_thc_rate(asal,   "FL", "L")
        rate_thd_fl = get_thc_rate(tujuan, "FL", "D")
        thc_full = q_full * (rate_thl_fl + rate_thd_fl)

        # THC EMPTY (MT) hanya di leg balikan
        q_empty = max(empty_flow.get((asal, tujuan), 0.0), 0.0)
        rate_thl_mt = get_thc_rate(asal,   "MT", "L")
        rate_thd_mt = get_thc_rate(tujuan, "MT", "D")
        thc_empty = q_empty * (rate_thl_mt + rate_thd_mt)

        subtotal = thc_full + thc_empty
        total += subtotal

        detail_rows.append([
            asal, tujuan, q_full, q_empty, subtotal
        ])

    df_detail = pd.DataFrame(
        detail_rows,
        columns=["Asal", "Tujuan", "Q_full", "Q_empty", "THC_leg"]
    )
    return total, df_detail




# ==========================================
# 3. UI DASHBOARD
# ==========================================
st.title("🚢 Kalkulasi Operasional Kapal")
st.markdown("---")

with st.sidebar:
    st.header("Input Data")
    selected_ship = st.selectbox("Pilih Kapal", df_kapal["Nama Kapal"])
    input_route = st.text_input("Rute (ex: SBY-JKT-MKS)", "SBY-JKT-MKS")
    harga_bbm = st.number_input("Harga BBM (Rp/Liter)", 10000, step=100)
    
        # >>> input baru: speed kapal
    ship_speed = st.number_input(
        "Kecepatan Kapal (knot)",
        min_value=1.0,
        max_value=30.0,
        value=20.0,
        step=0.5
    )
    
    # Reset Revenue Table jika rute berubah
    if 'last_route' not in st.session_state: st.session_state.last_route = ""
    if input_route != st.session_state.last_route:
        st.session_state.df_revenue = generate_revenue_template(input_route)
        st.session_state.last_route = input_route

if 'df_revenue' not in st.session_state: st.session_state.df_revenue = pd.DataFrame()

col1, col2 = st.columns([1, 2])

# --- PANEL KIRI: BIAYA ---
with col1:
    st.subheader("1. Estimasi Biaya")
    res, err = calculate_operational_cost(selected_ship, input_route, ship_speed)
    if err:
        st.error(err)
        total_cost = 0
    else:
        bbm_rp = res['Total_L'] * harga_bbm
        total_cost = res['TotalOps'] + bbm_rp
        
        st.metric("Total Jarak", f"{res['Jarak']:,.0f} NM")
        c1, c2 = st.columns(2)
        
        c1.metric("Total BBM (L)", f"{res['Total_L']:,.0f}")
        with c2:
        
            c2.metric("Est. Biaya BBM", format_rupiah_compact(bbm_rp))
        
        st.write(f"*Fixed Cost:* Rp {res['DOC']:,.0f}")
        st.write(f"*Port Cost:* Rp {res['PortCost']:,.0f}")
        st.success(f"### Total Cost (Tanpa THC): Rp {total_cost:,.0f}")

# --- PANEL KANAN: REVENUE (AUTO UPDATE) ---
with col2:
    st.subheader("2. Perencanaan Revenue")
    
    if not st.session_state.df_revenue.empty:
        # DATA EDITOR DENGAN CALLBACK
        # Kita menampilkan st.session_state.df_revenue secara langsung
        st.data_editor(
            st.session_state.df_revenue,
            column_config={
                "Kombinasi": st.column_config.TextColumn(disabled=True),
                "Port Asal": st.column_config.TextColumn(disabled=True),
                "Port Tujuan": st.column_config.TextColumn(disabled=True),
                "Jumlah Box": st.column_config.NumberColumn(required=True, min_value=0),
                "Harga/TEU (Rp)": st.column_config.NumberColumn(required=True, min_value=0, format="Rp %d"),
                "Total Revenue (Rp)": st.column_config.NumberColumn(disabled=True, format="Rp %d") 
            },
            hide_index=True,
            use_container_width=True,
            key="editor_revenue",    # Kunci unik untuk widget ini
            on_change=recalculate_revenue # <--- TRIGGER OTOMATIS SAAT DI-EDIT
        )

        # Summary Profit
        total_rev = st.session_state.df_revenue["Total Revenue (Rp)"].sum()
        total_box = st.session_state.df_revenue["Jumlah Box"].sum()
        total_thc, df_thc_detail = calculate_total_thc(
            st.session_state.df_revenue,
            input_route
        )
        
        st.markdown("### Summary")
        m1, m2, m3 = st.columns(3)
        m4 = st.columns(1)[0]
        m1.metric("Total Box", f"{total_box:,.0f}")
        m2.metric("Revenue", format_rupiah_compact(total_rev))
        
        profit = total_rev - total_cost - total_thc
        color = "normal" if profit > 0 else "off"

        m3.metric(
            "Net Profit (juta Rp)",
            format_rupiah_compact(profit),
            delta_color=color
        )
        m4.metric("Total THC (juta Rp)", format_rupiah_compact(total_thc))

        # opsional: tampilkan rincian THC per leg (buat cek logika)
        with st.expander("Rincian THC per Leg"):
            st.dataframe(df_thc_detail, use_container_width=True)

    else:
        st.info("Masukkan rute yang valid.")