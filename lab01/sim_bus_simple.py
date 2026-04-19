import random
import matplotlib.pyplot as plt
import heapq

def simulate(seed=None):
    if seed is not None:
        random.seed(seed)

    SIM_TIME = 28800  # 8h in seconds

    # Shared state: last bus arrival time at each stop
    lastp = 0.0  # Stop 1
    lastq = 0.0  # Stop 2

    # Event heap: (time, bus_id, action)
    events = []
    heapq.heappush(events, (0.0, 0, 'arrive_stop1'))
    heapq.heappush(events, (300.0, 1, 'arrive_stop1'))

    # Data collection (equivalent to GRAPH C1,P$INT)
    graph_times = []
    graph_ints = []

    while events:
        time, bus, action = heapq.heappop(events)

        if time > SIM_TIME:
            break

        if action == 'arrive_stop1':
            interval = time - lastp
            dwell = interval * 0.3
            lastp = time
            graph_times.append(time)
            graph_ints.append(interval)
            travel = random.uniform(165, 195)  # ADVANCE 180,15
            heapq.heappush(events, (time + dwell + travel, bus, 'arrive_stop2'))

        elif action == 'arrive_stop2':
            interval = time - lastq
            dwell = interval * 0.3
            lastq = time
            graph_times.append(time)
            graph_ints.append(interval)
            travel = random.uniform(165, 195)  # ADVANCE 180,15
            heapq.heappush(events, (time + dwell + travel, bus, 'arrive_stop1'))

    return graph_times, graph_ints


# --- Single run with graph ---
times, ints = simulate(seed=42)

plt.figure(figsize=(10, 4.5))
plt.plot(times, ints, 'r-', linewidth=0.7)
plt.xlabel('TIME')
plt.ylabel('INT')
plt.title('INT', color='red', fontweight='bold')
plt.xlim(0, 28800)
plt.ylim(0, max(ints) * 1.1)
plt.xticks(range(0, 28801, 3000))
plt.grid(True, alpha=0.2)
plt.tight_layout()
plt.savefig('/home/claude/bus_bunching_python.png', dpi=150, bbox_inches='tight')
print(f"Total data points: {len(times)}")
print(f"Mean INT: {sum(ints)/len(ints):.1f}")
print(f"Std INT:  {(sum((x - sum(ints)/len(ints))**2 for x in ints)/len(ints))**0.5:.1f}")
print("Graph saved.")
