"""
Model ampliat amb demanda variable (3 busos, 5 parades)
24000s = 24h simulades (1000s = 1h)
3 nivells de demanda: nit, dia, hora punta
"""
import random
import heapq
import matplotlib.pyplot as plt
import numpy as np
import statistics

def demand_multiplier(time):
    """Retorna multiplicador de demanda segons franja horària"""
    h = time / 1000  # hora del dia
    if h < 6:       return 0.1   # Nit: gairebé ningú
    elif h < 9:     return 1.5   # Matí punta
    elif h < 15:    return 1.0   # Dia normal
    elif h < 18:    return 2.0   # Tarda punta (màxima demanda)
    elif h < 22:    return 1.0   # Vespre normal
    else:           return 0.1   # Nit

def simulate(seed=42, n_buses=3, n_stops=5, sim_time=24000):
    random.seed(seed)
    np.random.seed(seed)

    # Taxes base d'arribada (passatgers/segon)
    base_rates = [1/60, 1/30, 1/30, 1/30, 1/60]

    # Temps viatge entre parades
    travel_times = [(120, 10), (150, 12), (150, 12), (120, 10), (180, 15)]

    # Estat
    pax_at_stop = [0.0] * n_stops
    last_pax_update = [0.0] * n_stops
    last_bus_at_stop = [0.0] * n_stops

    # Dades
    headway_data = {s: {'times': [], 'headways': []} for s in range(n_stops)}
    pax_data = {s: {'times': [], 'pax_boarding': []} for s in range(n_stops)}

    # Inicialitzar busos (comencen a les 6h = 6000s)
    events = []
    for b in range(n_buses):
        heapq.heappush(events, (6000 + b * 200, b, 'arrive', 0))

    while events:
        time, bus, action, stop = heapq.heappop(events)
        if time > sim_time:
            break

        if action == 'arrive':
            # Acumular passatgers amb demanda variable
            dt = time - last_pax_update[stop]
            # Discretitzem en intervals petits per capturar els canvis de demanda
            t_start = last_pax_update[stop]
            accumulated = 0.0
            step = 100  # cada 100s recalculem la taxa
            t = t_start
            while t < time:
                t_end = min(t + step, time)
                interval = t_end - t
                rate = base_rates[stop] * demand_multiplier(t)
                accumulated += rate * interval
                t = t_end
            n_pax = np.random.poisson(max(0, accumulated))
            pax_at_stop[stop] = max(0, pax_at_stop[stop] + n_pax)
            last_pax_update[stop] = time

            # Headway
            headway = time - last_bus_at_stop[stop]
            last_bus_at_stop[stop] = time
            headway_data[stop]['times'].append(time)
            headway_data[stop]['headways'].append(headway)

            # Embarcar
            n_boarding = int(pax_at_stop[stop])
            pax_data[stop]['times'].append(time)
            pax_data[stop]['pax_boarding'].append(n_boarding)

            dwell = 0
            for _ in range(n_boarding):
                if random.random() < 0.05:
                    dwell += random.uniform(8, 15)
                else:
                    dwell += random.uniform(2, 4)
            pax_at_stop[stop] = 0

            # Viatjar
            next_stop = (stop + 1) % n_stops
            mean_t, std_t = travel_times[stop]
            travel = max(60, random.gauss(mean_t, std_t))
            heapq.heappush(events, (time + dwell + travel, bus, 'arrive', next_stop))

    return headway_data, pax_data

# --- Executar ---
hd, pd_ = simulate(seed=42)

# --- Gràfic 1: Headway a parada cèntrica (parada 2) ---
fig, axes = plt.subplots(3, 1, figsize=(14, 11), sharex=True)

# Fons amb franges horàries
colors_bg = [
    (0, 6000, '#1a1a2e', 'Nit'),
    (6000, 9000, '#ff9966', 'Matí punta'),
    (9000, 15000, '#ffffcc', 'Dia'),
    (15000, 18000, '#ff6666', 'Tarda punta'),
    (18000, 22000, '#ffffcc', 'Vespre'),
    (22000, 24000, '#1a1a2e', 'Nit'),
]

for ax in axes:
    for t0, t1, col, label in colors_bg:
        ax.axvspan(t0, t1, alpha=0.15, color=col)

# Gràfic headway parada 2
ax = axes[0]
ax.plot(hd[2]['times'], hd[2]['headways'], 'b-', linewidth=0.7)
ax.set_ylabel('Headway (s)')
ax.set_title('Headway — Parada 2 (cèntrica, λ_base=1/30)')
ax.set_ylim(0, max(hd[2]['headways'])*1.1)
ax.grid(True, alpha=0.2)

# Gràfic headway parada 0
ax = axes[1]
ax.plot(hd[0]['times'], hd[0]['headways'], 'r-', linewidth=0.7)
ax.set_ylabel('Headway (s)')
ax.set_title('Headway — Parada 0 (perifèrica, λ_base=1/60)')
ax.set_ylim(0, max(hd[0]['headways'])*1.1)
ax.grid(True, alpha=0.2)

# Gràfic passatgers embarcats parada 2
ax = axes[2]
ax.bar(pd_[2]['times'], pd_[2]['pax_boarding'], width=80, color='steelblue', alpha=0.7)
ax.set_ylabel('Passatgers embarcats')
ax.set_title('Passatgers per bus — Parada 2 (cèntrica)')
ax.set_xlabel('Temps (s)    [0-6: nit | 6-9: matí punta | 9-15: dia | 15-18: tarda punta | 18-22: vespre | 22-24: nit]')
ax.grid(True, alpha=0.2)

# Etiquetes d'hores a l'eix X
hours = list(range(0, 25, 2))
ax.set_xticks([h*1000 for h in hours])
ax.set_xticklabels([f'{h}h' for h in hours])
axes[0].set_xticks([h*1000 for h in hours])
axes[1].set_xticks([h*1000 for h in hours])

plt.suptitle('Demanda variable: 3 busos, 5 parades, 24h', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('/home/claude/demanda_variable.png', dpi=150)
print("Gràfic guardat!")

# Stats per franja
for label, t0, t1 in [("Nit (0-6h)", 0, 6000), ("Matí punta (6-9h)", 6000, 9000),
                        ("Dia (9-15h)", 9000, 15000), ("Tarda punta (15-18h)", 15000, 18000),
                        ("Vespre (18-22h)", 18000, 22000)]:
    hws = [h for t, h in zip(hd[2]['times'], hd[2]['headways']) if t0 <= t < t1]
    if len(hws) > 1:
        print(f"{label}: headway={statistics.mean(hws):.0f}±{statistics.stdev(hws):.0f}s, n={len(hws)}")
    elif hws:
        print(f"{label}: headway={hws[0]:.0f}s, n=1")
    else:
        print(f"{label}: sense dades (busos no operen)")
