"""
Model ampliat base: 3 busos, 5 parades, passatgers explícits
- Arribades exponencials a cada parada (taxa diferent per parada)
- Temps embarcament individual (+ PMR)
- Viatge entre parades amb soroll
"""
import random
import heapq
import matplotlib.pyplot as plt

def simulate(seed=42, n_buses=3, n_stops=5, sim_time=28800):
    random.seed(seed)

    # --- Paràmetres per parada ---
    # Taxa arribada passatgers (passatgers/segon)
    # Parades 1,5 = perifèriques (1 cada 60s), parades 2,3,4 = cèntriques (1 cada 30s)
    arrival_rates = [1/60, 1/30, 1/30, 1/30, 1/60]

    # Temps viatge entre parades consecutives (s): mitjana i desviació
    travel_times = [(120, 10), (150, 12), (150, 12), (120, 10), (180, 15)]  # parada i -> i+1 (circular)

    # --- Estat global ---
    # Passatgers acumulats a cada parada (comptador continu)
    pax_at_stop = [0.0] * n_stops
    last_pax_update = [0.0] * n_stops  # últim moment que hem actualitzat pax
    last_bus_at_stop = [0.0] * n_stops  # últim bus que ha passat (per headway)

    # --- Recollida de dades ---
    headway_data = {s: {'times': [], 'headways': []} for s in range(n_stops)}

    # --- Events: (time, bus_id, 'arrive', stop_index) ---
    events = []
    spacing = sim_time / (n_buses * n_stops)  # espaiament inicial raonable
    for b in range(n_buses):
        t0 = b * (sim_time / n_buses / n_stops * n_stops)  # espaiats uniformement
        t0 = b * 200  # cada 200s surt un bus
        heapq.heappush(events, (t0, b, 'arrive', 0))

    while events:
        time, bus, action, stop = heapq.heappop(events)
        if time > sim_time:
            break

        if action == 'arrive':
            # 1) Actualitzar passatgers acumulats des de l'última actualització
            dt = time - last_pax_update[stop]
            # Generem quants passatgers han arribat en dt segons (Poisson)
            expected = arrival_rates[stop] * dt
            n_pax = random.randint(max(0, int(expected - 1)), int(expected + 1))
            # Millor: usar Poisson real
            import numpy as np  # lazy import
            n_pax = np.random.poisson(arrival_rates[stop] * dt)
            pax_at_stop[stop] += n_pax
            last_pax_update[stop] = time

            # 2) Registrar headway
            headway = time - last_bus_at_stop[stop]
            last_bus_at_stop[stop] = time
            headway_data[stop]['times'].append(time)
            headway_data[stop]['headways'].append(headway)

            # 3) Embarcar passatgers
            n_boarding = int(pax_at_stop[stop])
            dwell = 0
            for _ in range(n_boarding):
                if random.random() < 0.05:  # 5% PMR
                    dwell += random.uniform(8, 15)
                else:
                    dwell += random.uniform(2, 4)
            pax_at_stop[stop] = 0  # tots pugen (capacitat infinita)

            # 4) Viatjar a la següent parada
            next_stop = (stop + 1) % n_stops
            mean_t, std_t = travel_times[stop]
            travel = max(60, random.gauss(mean_t, std_t))

            heapq.heappush(events, (time + dwell + travel, bus, 'arrive', next_stop))

    return headway_data

# --- Executar i graficar ---
data = simulate(seed=42)

fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

# Parada 0 (perifèrica)
ax = axes[0]
ax.plot(data[0]['times'], data[0]['headways'], 'r-', linewidth=0.6)
ax.set_ylabel('Headway (s)')
ax.set_title('Parada 0 (perifèrica, λ=1/60)', fontsize=11)
ax.set_ylim(0, max(data[0]['headways'])*1.1 if data[0]['headways'] else 1000)
ax.grid(True, alpha=0.2)

# Parada 2 (cèntrica)
ax = axes[1]
ax.plot(data[2]['times'], data[2]['headways'], 'b-', linewidth=0.6)
ax.set_ylabel('Headway (s)')
ax.set_title('Parada 2 (cèntrica, λ=1/30)', fontsize=11)
ax.set_ylim(0, max(data[2]['headways'])*1.1 if data[2]['headways'] else 1000)
ax.grid(True, alpha=0.2)

# Parada 4 (perifèrica)
ax = axes[2]
ax.plot(data[4]['times'], data[4]['headways'], 'g-', linewidth=0.6)
ax.set_ylabel('Headway (s)')
ax.set_title('Parada 4 (perifèrica, λ=1/60)', fontsize=11)
ax.set_ylim(0, max(data[4]['headways'])*1.1 if data[4]['headways'] else 1000)
ax.grid(True, alpha=0.2)
ax.set_xlabel('Temps (s)')

plt.suptitle('Model ampliat: 3 busos, 5 parades — Headway temporal', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('/home/claude/ampliat_v1.png', dpi=150)
print("Gràfic guardat!")

# Stats
for s in [0, 2, 4]:
    hws = data[s]['headways'][3:]  # skip first few (transient)
    if hws:
        import statistics
        print(f"Parada {s}: headway mitjà={statistics.mean(hws):.1f}s, std={statistics.stdev(hws):.1f}s, n={len(hws)}")
