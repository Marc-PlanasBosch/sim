"""
=============================================================
  SIM Lab01 — Model ampliat final (Millores A + B + C)
  
  Millora A: Demanda variable al llarg del dia
  Millora B: Capacitat finita (100 pax) i passatgers rebutjats
  Millora C: Holding (200s) + Leapfrogging
  
  3 busos, 5 parades, 24h (24000s, on 1000s = 1h)
  ✅ Llest per executar a Google Colab sense cap modificació
=============================================================
"""

import random, heapq, statistics
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Franges horàries ──────────────────────────────────────────────────────────
def demand_multiplier(time):
    h = time / 1000
    if h < 6:    return 0.15   # Nit
    elif h < 9:  return 1.5    # Matí punta
    elif h < 15: return 1.0    # Dia normal
    elif h < 18: return 2.5    # Tarda punta
    elif h < 22: return 1.0    # Vespre
    else:        return 0.15   # Nit

# ── Simulació ─────────────────────────────────────────────────────────────────
def simulate(seed=42, n_buses=3, n_stops=5, sim_time=24000,
             bus_capacity=100, min_headway=200,
             use_leapfrog=False, leapfrog_hw_threshold=100):
    """
    Paràmetres:
      bus_capacity          : aforament màxim per bus (Millora B)
      min_headway           : headway mínim forçat a la terminal (Millora C - Holding)
      use_leapfrog          : activar leapfrogging (Millora C)
      leapfrog_hw_threshold : llindar de headway per activar leapfrog (en segons)
    """
    random.seed(seed)
    np.random.seed(seed)

    # Paràmetres de la línia
    base_rates   = [1/60, 1/30, 1/30, 1/30, 1/60]   # perifèrica / cèntrica
    travel_times = [(120,10),(150,12),(150,12),(120,10),(180,15)]  # (mitjana, std)

    # Estat de les parades
    waiting          = [[] for _ in range(n_stops)]   # arrival_times dels passatgers
    last_pax_update  = [0.0] * n_stops
    last_bus_time    = [None] * n_stops
    last_depart_stop0 = None                           # per al holding

    # Estat dels busos
    bus_load        = [0] * n_buses
    bus_arrive_time = {b: {} for b in range(n_buses)} # bus -> {stop -> temps arribada}
    bus_depart_est  = {b: {} for b in range(n_buses)} # bus -> {stop -> temps sortida est.}

    # Recollida de dades
    headway_data   = {s: {'times': [], 'headways': []}  for s in range(n_stops)}
    rejected_data  = {s: {'times': [], 'rejected': []}  for s in range(n_stops)}
    occupancy_data = {b: {'times': [], 'occupancy': []} for b in range(n_buses)}
    waiting_times  = []
    holding_log    = []   # (time, bus, hold_duration)
    leapfrog_log   = []   # (time, bus, stop_leapfrogged)

    # Inicialització: busos espaiats 200s
    events = []
    for b in range(n_buses):
        heapq.heappush(events, (b * 200, b, 0))

    # ── Bucle principal ───────────────────────────────────────────────────────
    while events:
        time, bus, stop = heapq.heappop(events)
        if time > sim_time:
            break

        # 1) Acumular passatgers nous (integració per trossos de 50s)
        dt = time - last_pax_update[stop]
        if dt > 0:
            t, acc = last_pax_update[stop], 0.0
            while t < time:
                t_end = min(t + 50, time)
                acc  += base_rates[stop] * demand_multiplier(t) * (t_end - t)
                t     = t_end
            n_new = np.random.poisson(max(0, acc))
            for _ in range(n_new):
                waiting[stop].append(time - random.uniform(0, dt))
            last_pax_update[stop] = time

        # 2) Headway
        if last_bus_time[stop] is not None:
            headway_data[stop]['times'].append(time)
            headway_data[stop]['headways'].append(time - last_bus_time[stop])
        last_bus_time[stop] = time
        bus_arrive_time[bus][stop] = time

        # ── HOLDING (Millora C) ───────────────────────────────────────────────
        # A la terminal (parada 0), forçar headway mínim de 200s
        hold_time = 0
        if stop == 0 and last_depart_stop0 is not None:
            elapsed = time - last_depart_stop0
            if elapsed < min_headway:
                hold_time = min_headway - elapsed
                holding_log.append((time, bus, hold_time))

        # 3) Baixada: prob. 1/(n_stops-1) de baixar a cada parada (Millora B)
        if bus_load[bus] > 0:
            alighting = np.random.binomial(bus_load[bus], 1.0 / (n_stops - 1))
            bus_load[bus] -= min(alighting, bus_load[bus])

        # 4) Pujada amb capacitat finita (Millora B)
        free_seats = bus_capacity - bus_load[bus]
        n_waiting  = len(waiting[stop])
        n_boarding = min(free_seats, n_waiting)
        n_rejected = n_waiting - n_boarding

        # Pugen els que porten més estona (FIFO per temps d'arribada)
        for arr_t in sorted(waiting[stop])[:n_boarding]:
            wt_val = time - arr_t
            if wt_val >= 0:
                waiting_times.append(wt_val)
        waiting[stop]  = sorted(waiting[stop])[n_boarding:]
        bus_load[bus] += n_boarding

        rejected_data[stop]['times'].append(time)
        rejected_data[stop]['rejected'].append(n_rejected)
        occupancy_data[bus]['times'].append(time)
        occupancy_data[bus]['occupancy'].append(bus_load[bus])

        # 5) Temps d'aturada emergent (Millora B)
        dwell = sum(
            random.uniform(8, 15) if random.random() < 0.05 else random.uniform(2, 4)
            for _ in range(n_boarding)
        )

        depart_time = time + hold_time + dwell
        bus_depart_est[bus][stop] = depart_time
        if stop == 0:
            last_depart_stop0 = depart_time

        # ── LEAPFROGGING (Millora C) ──────────────────────────────────────────
        # Si un bus lent és a next_stop i van en comboi (hw < llindar),
        # el bus ràpid hi arriba just 0.1s abans que el lent surti,
        # recull la cua restant i surt primer → inversió d'ordre.
        next_stop = (stop + 1) % n_stops
        mean_t, std_t = travel_times[stop]
        travel = max(60, random.gauss(mean_t, std_t))
        arrival_at_next = depart_time + travel
        lf_applied = False

        if use_leapfrog:
            for b2 in range(n_buses):
                if b2 == bus:
                    continue
                arr2 = bus_arrive_time[b2].get(next_stop)
                dep2 = bus_depart_est[b2].get(next_stop)
                if arr2 is None or dep2 is None:
                    continue
                # El bus b2 és a next_stop i encara hi serà quan hi arribem
                if dep2 > arrival_at_next:
                    hw_between = time - arr2
                    if hw_between < leapfrog_hw_threshold:
                        # Leapfrog: arribar 0.1s abans que el lent surti
                        leapfrog_arrival = dep2 - 0.1
                        if leapfrog_arrival > time:
                            leapfrog_log.append((time, bus, next_stop))
                            heapq.heappush(events, (leapfrog_arrival, bus, next_stop))
                            lf_applied = True
                            break

        if not lf_applied:
            heapq.heappush(events, (arrival_at_next, bus, next_stop))

    return headway_data, rejected_data, occupancy_data, waiting_times, holding_log, leapfrog_log


# ── Execució dels 3 escenaris ─────────────────────────────────────────────────
print("Simulant els 3 escenaris...")

hd0, rd0, od0, wt0, hl0, ll0 = simulate(seed=42, min_headway=0,   use_leapfrog=False)
hd1, rd1, od1, wt1, hl1, ll1 = simulate(seed=42, min_headway=200, use_leapfrog=False)
hd2, rd2, od2, wt2, hl2, ll2 = simulate(seed=42, min_headway=200, use_leapfrog=True)

def stats(hd, wt, hl, ll, rd):
    hws = hd[2]['headways']
    m   = statistics.mean(hws)
    s   = statistics.stdev(hws) if len(hws) > 1 else 0
    r   = sum(sum(rd[s2]['rejected']) for s2 in rd)
    wt_m = statistics.mean(wt) if wt else 0
    return m, s, r, wt_m

m0,s0,r0,w0 = stats(hd0,wt0,hl0,ll0,rd0)
m1,s1,r1,w1 = stats(hd1,wt1,hl1,ll1,rd1)
m2,s2,r2,w2 = stats(hd2,wt2,hl2,ll2,rd2)

print("\n=== RESUM COMPARATIU (Parada 2, cèntrica) ===")
print(f"{'Escenari':<35} {'HW mitjà':>10} {'HW std':>8} {'CV':>6} {'WT mitjà':>10} {'Rebutjats':>11} {'Holding':>8} {'Leapfrog':>9}")
print("-"*100)
for label,m,s,r,w,hl_,ll_ in [
    ("Sense regulació (A+B)",    m0,s0,r0,w0,hl0,ll0),
    ("Holding 200s (A+B+C)",     m1,s1,r1,w1,hl1,ll1),
    ("Holding+Leapfrog (A+B+C)", m2,s2,r2,w2,hl2,ll2),
]:
    print(f"{label:<35} {m:>9.0f}s {s:>7.0f}s {s/m*100:>5.0f}% {w:>9.0f}s {r:>11} {len(hl_):>8} {len(ll_):>9}")

# ── Estadístiques per franja (millor escenari) ────────────────────────────────
franges_labels = ['Nit (0-6h)','Matí punta (6-9h)','Dia (9-15h)',
                  'Tarda punta (15-18h)','Vespre (18-22h)','Nit (22-24h)']
franges_ranges = [(0,6000),(6000,9000),(9000,15000),(15000,18000),(18000,22000),(22000,24000)]

print(f"\n=== ESTADÍSTIQUES PER FRANJA — HOLDING + LEAPFROG (Parada 2) ===")
print(f"{'Franja':<25} {'HW mitjà':>10} {'Std':>8} {'CV':>6} {'Rebutjats':>11} {'N':>5}")
print("-"*66)
for label,(t0,t1) in zip(franges_labels, franges_ranges):
    hws = [h for t,h in zip(hd2[2]['times'], hd2[2]['headways']) if t0 <= t < t1]
    rej = [r for t,r in zip(rd2[2]['times'], rd2[2]['rejected']) if t0 <= t < t1]
    hw_m = f"{statistics.mean(hws):.0f}s"  if len(hws) > 1 else "—"
    hw_s = f"{statistics.stdev(hws):.0f}s" if len(hws) > 1 else "—"
    cv   = f"{statistics.stdev(hws)/statistics.mean(hws)*100:.0f}%" if len(hws) > 1 else "—"
    print(f"{label:<25} {hw_m:>10} {hw_s:>8} {cv:>6} {str(sum(rej)) if rej else '0':>11} {len(hws):>5}")

# ── Configuració gràfics ──────────────────────────────────────────────────────
shade_franges = [
    (0,     6000,  '#2c3e50', 0.12), (6000,  9000,  '#e67e22', 0.15),
    (9000,  15000, '#f1c40f', 0.10), (15000, 18000, '#e74c3c', 0.15),
    (18000, 22000, '#f1c40f', 0.10), (22000, 24000, '#2c3e50', 0.12),
]
hours   = list(range(0, 25, 2))
xticks  = [h * 1000 for h in hours]
xlabels = [f'{h}h' for h in hours]

def shade_ax(ax):
    for t0,t1,col,a in shade_franges:
        ax.axvspan(t0, t1, alpha=a, color=col)
    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels)
    ax.set_xlim(0, 24000)
    ax.grid(True, alpha=0.2)

legend_patches = [
    mpatches.Patch(color='#2c3e50', alpha=0.5, label='Nit ×0.15'),
    mpatches.Patch(color='#e67e22', alpha=0.5, label='Matí punta ×1.5'),
    mpatches.Patch(color='#f1c40f', alpha=0.5, label='Dia ×1.0'),
    mpatches.Patch(color='#e74c3c', alpha=0.5, label='Tarda punta ×2.5'),
]

# ══════════════════════════════════════════════════════════════════════════════
# FIGURA 1 — Headway dels 3 escenaris + Ocupació
# ══════════════════════════════════════════════════════════════════════════════
fig1, axes1 = plt.subplots(4, 1, figsize=(15, 14), sharex=True)
for ax in axes1:
    shade_ax(ax)

for ax, hd_, hl_, ll_, col, label, m, s, w in [
    (axes1[0], hd0, hl0, ll0, '#e74c3c', 'Sense regulació (A+B)',    m0, s0, w0),
    (axes1[1], hd1, hl1, ll1, '#3498db', 'Holding 200s (A+B+C)',     m1, s1, w1),
    (axes1[2], hd2, hl2, ll2, '#2ecc71', 'Holding + Leapfrog (A+B+C)', m2, s2, w2),
]:
    ax.plot(hd_[2]['times'], hd_[2]['headways'], color=col, lw=0.8, marker='.', ms=2)
    ax.axhline(200, color='gray', lw=1, linestyle='--', alpha=0.6, label='Objectiu 200s')
    ax.text(0.99, 0.95, f"CV={s/m*100:.0f}%  HW={m:.0f}s  WT={w:.0f}s",
            transform=ax.transAxes, ha='right', va='top', fontsize=9,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    if hl_:
        ax.scatter([h[0] for h in hl_], [20]*len(hl_), marker='v', color='green',
                   s=18, zorder=5, label=f'Holding ({len(hl_)})')
    if ll_:
        ax.scatter([e[0] for e in ll_], [40]*len(ll_), marker='^', color='purple',
                   s=35, zorder=5, label=f'Leapfrog ({len(ll_)})')
    ax.set_ylabel('Headway (s)')
    ax.set_title(f'Headway Parada 2 — {label}', fontsize=10)
    ax.legend(loc='upper right', fontsize=7, ncol=3)

ax = axes1[3]
bus_colors = ['#1abc9c', '#e74c3c', '#3498db']
for b in range(3):
    if od2[b]['times']:
        ax.plot(od2[b]['times'], od2[b]['occupancy'],
                color=bus_colors[b], lw=0.8, alpha=0.85, label=f'Bus {b}')
ax.axhline(100, color='black', lw=1, linestyle='--', label='Capacitat màx. (100)')
ax.set_ylabel('Passatgers a bord')
ax.set_ylim(0, 115)
ax.set_xlabel('Hora del dia')
ax.set_title('Ocupació dels busos — Holding + Leapfrog', fontsize=10)
ax.legend(loc='upper left', fontsize=7, ncol=4)

fig1.legend(handles=legend_patches, loc='lower center', ncol=4,
            fontsize=9, bbox_to_anchor=(0.5, -0.01))
plt.suptitle('Millora A+B+C: Comparació dels escenaris de regulació — Parada 2 (cèntrica)',
             fontsize=13, fontweight='bold')
plt.tight_layout(rect=[0, 0.03, 1, 1])
plt.show()

# ══════════════════════════════════════════════════════════════════════════════
# FIGURA 2 — Histograma WT + Barres comparatives + Rebutjats per franja
# ══════════════════════════════════════════════════════════════════════════════
fig2, axes2 = plt.subplots(1, 3, figsize=(18, 5))

# (a) Histograma temps d'espera
ax = axes2[0]
ax.hist(wt0, bins=50, alpha=0.5, color='#e74c3c', label=f'Sense reg. (μ={w0:.0f}s)')
ax.hist(wt1, bins=50, alpha=0.5, color='#3498db', label=f'Holding    (μ={w1:.0f}s)')
ax.hist(wt2, bins=50, alpha=0.5, color='#2ecc71', label=f'Hold+Leap  (μ={w2:.0f}s)')
ax.set_xlabel("Temps d'espera (s)")
ax.set_ylabel('Passatgers')
ax.set_title("Distribució del temps d'espera per escenari", fontsize=10)
ax.legend(fontsize=8)
ax.grid(True, alpha=0.2)

# (b) Barres comparatives de mètriques clau
ax = axes2[1]
labels_esc = ['Sense\nreg.', 'Holding\n200s', 'Holding+\nLeapfrog']
x     = np.arange(3)
width = 0.28
b1 = ax.bar(x-width, [m0,m1,m2], width, label='HW mitjà (s)',  color='#3498db', alpha=0.85)
b2 = ax.bar(x,       [s0,s1,s2], width, label='HW std (s)',    color='#e67e22', alpha=0.85)
b3 = ax.bar(x+width, [w0,w1,w2], width, label='WT mitjà (s)',  color='#2ecc71', alpha=0.85)
ax.set_xticks(x)
ax.set_xticklabels(labels_esc, fontsize=9)
ax.set_ylabel('Segons')
ax.set_title('Comparació de mètriques per escenari', fontsize=10)
ax.legend(fontsize=8)
ax.grid(True, alpha=0.2, axis='y')
for bar in [b1, b2, b3]:
    for rect in bar:
        h = rect.get_height()
        ax.annotate(f'{h:.0f}', xy=(rect.get_x()+rect.get_width()/2, h),
                    xytext=(0,2), textcoords='offset points',
                    ha='center', va='bottom', fontsize=7)

# (c) Rebutjats per franja: Holding vs Holding+Leapfrog
ax = axes2[2]
franges_short = ['Nit\n0-6h','Matí\npunta','Dia\n9-15h','Tarda\npunta','Vespre','Nit\n22-24h']
rej1 = [sum(r for t,r in zip(rd1[2]['times'], rd1[2]['rejected']) if t0<=t<t1)
        for t0,t1 in franges_ranges]
rej2 = [sum(r for t,r in zip(rd2[2]['times'], rd2[2]['rejected']) if t0<=t<t1)
        for t0,t1 in franges_ranges]
x2 = np.arange(len(franges_ranges))
ax.bar(x2-0.2, rej1, 0.4, label='Holding',          color='#3498db', alpha=0.85)
ax.bar(x2+0.2, rej2, 0.4, label='Holding+Leapfrog', color='#2ecc71', alpha=0.85)
ax.set_xticks(x2)
ax.set_xticklabels(franges_short, fontsize=8)
ax.set_ylabel('Passatgers rebutjats (Parada 2)')
ax.set_title('Rebutjats per franja: Holding vs Holding+Leapfrog', fontsize=10)
ax.legend(fontsize=8)
ax.grid(True, alpha=0.2, axis='y')

plt.suptitle("Millora A+B+C: Anàlisi comparativa de les estratègies de regulació",
             fontsize=12, fontweight='bold')
plt.tight_layout()
plt.show()
