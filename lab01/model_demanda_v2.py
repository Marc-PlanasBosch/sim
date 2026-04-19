"""
Model ampliat amb demanda variable — v2
Busos circulen 24h sense parar, demanda variable amb 3 nivells
24000s (1000s = 1h)
"""
import random, heapq, statistics
import matplotlib.pyplot as plt
import numpy as np

def demand_multiplier(time):
    h = time / 1000
    if h < 6:       return 0.15  # Nit: poca gent però n'hi ha
    elif h < 9:     return 1.5   # Matí punta
    elif h < 15:    return 1.0   # Dia normal
    elif h < 18:    return 2.5   # Tarda punta (agressiu)
    elif h < 22:    return 1.0   # Vespre
    else:           return 0.15  # Nit

def simulate(seed=42, n_buses=3, n_stops=5, sim_time=24000):
    random.seed(seed)
    np.random.seed(seed)

    base_rates = [1/60, 1/30, 1/30, 1/30, 1/60]
    travel_times = [(120, 10), (150, 12), (150, 12), (120, 10), (180, 15)]

    pax_at_stop = [0.0] * n_stops
    last_pax_update = [0.0] * n_stops
    last_bus_at_stop = [None] * n_stops  # None = cap bus ha passat encara

    headway_data = {s: {'times': [], 'headways': []} for s in range(n_stops)}
    pax_data = {s: {'times': [], 'pax_boarding': []} for s in range(n_stops)}

    # Busos comencen a t=0, espaiats
    events = []
    for b in range(n_buses):
        heapq.heappush(events, (b * 200, b, 'arrive', 0))

    while events:
        time, bus, action, stop = heapq.heappop(events)
        if time > sim_time:
            break

        # Acumular passatgers amb demanda variable (integrar per trossos)
        dt = time - last_pax_update[stop]
        if dt > 0:
            t = last_pax_update[stop]
            accumulated = 0.0
            step = 50
            while t < time:
                t_end = min(t + step, time)
                rate = base_rates[stop] * demand_multiplier(t)
                accumulated += rate * (t_end - t)
                t = t_end
            n_pax = np.random.poisson(max(0, accumulated))
            pax_at_stop[stop] += n_pax
        last_pax_update[stop] = time

        # Headway (només si ja ha passat un bus abans)
        if last_bus_at_stop[stop] is not None:
            headway = time - last_bus_at_stop[stop]
            headway_data[stop]['times'].append(time)
            headway_data[stop]['headways'].append(headway)
        last_bus_at_stop[stop] = time

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

        next_stop = (stop + 1) % n_stops
        mean_t, std_t = travel_times[stop]
        travel = max(60, random.gauss(mean_t, std_t))
        heapq.heappush(events, (time + dwell + travel, bus, 'arrive', next_stop))

    return headway_data, pax_data

hd, pd_ = simulate(seed=42)

# --- Gràfic ---
fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

# Franges horàries
franges = [
    (0, 6000, '#2c3e50', 0.12), (6000, 9000, '#e67e22', 0.15),
    (9000, 15000, '#f1c40f', 0.10), (15000, 18000, '#e74c3c', 0.15),
    (18000, 22000, '#f1c40f', 0.10), (22000, 24000, '#2c3e50', 0.12),
]
for ax in axes:
    for t0, t1, col, a in franges:
        ax.axvspan(t0, t1, alpha=a, color=col)

# Headway parada 2 (cèntrica)
ax = axes[0]
ax.plot(hd[2]['times'], hd[2]['headways'], 'b-', linewidth=0.7, marker='.', markersize=2)
ax.set_ylabel('Headway (s)')
ax.set_title('Headway — Parada 2 (cèntrica, λ_base=1/30)', fontsize=11)
ax.grid(True, alpha=0.2)

# Headway parada 0 (perifèrica)
ax = axes[1]
ax.plot(hd[0]['times'], hd[0]['headways'], 'r-', linewidth=0.7, marker='.', markersize=2)
ax.set_ylabel('Headway (s)')
ax.set_title('Headway — Parada 0 (perifèrica, λ_base=1/60)', fontsize=11)
ax.grid(True, alpha=0.2)

# Passatgers embarcats parada 2
ax = axes[2]
ax.bar(pd_[2]['times'], pd_[2]['pax_boarding'], width=60, color='steelblue', alpha=0.7)
ax.set_ylabel('Passatgers')
ax.set_title('Passatgers embarcats per bus — Parada 2 (cèntrica)', fontsize=11)
ax.grid(True, alpha=0.2)
ax.set_xlabel('Hora del dia     [■ Nit ×0.15 | ■ Matí punta ×1.5 | ■ Dia ×1.0 | ■ Tarda punta ×2.5 | ■ Vespre ×1.0]')

# Eix X en hores
hours = list(range(0, 25, 2))
for a in axes:
    a.set_xticks([h*1000 for h in hours])
    a.set_xticklabels([f'{h}h' for h in hours])
    a.set_xlim(0, 24000)

plt.suptitle('Demanda variable: 3 busos, 5 parades, 24h', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('/home/claude/demanda_v2.png', dpi=150)
print("Gràfic guardat!\n")

# Stats per franja
print(f"{'Franja':<25} {'Headway P2':>12} {'Std':>8} {'N':>5}")
print("-"*52)
for label, t0, t1 in [("Nit (0-6h)",0,6000), ("Matí punta (6-9h)",6000,9000),
                        ("Dia (9-15h)",9000,15000), ("Tarda punta (15-18h)",15000,18000),
                        ("Vespre (18-22h)",18000,22000), ("Nit (22-24h)",22000,24000)]:
    hws = [h for t, h in zip(hd[2]['times'], hd[2]['headways']) if t0 <= t < t1]
    if len(hws) > 1:
        print(f"{label:<25} {statistics.mean(hws):>10.0f}s {statistics.stdev(hws):>7.0f}s {len(hws):>4}")
    elif len(hws) == 1:
        print(f"{label:<25} {hws[0]:>10.0f}s {'—':>7} {1:>4}")
    else:
        print(f"{label:<25} {'—':>10} {'—':>7} {0:>4}")
