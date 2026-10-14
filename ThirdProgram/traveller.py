import sys, csv, math, time, heapq, random, argparse


def dijkstra(n, E, K, C):
    adj = [[] for _ in range(n + 1)]
    for i, (u, v, p) in enumerate(E):
        adj[u].append((v, p, i))
    dist, par = {(1, 0, 0): 0}, {}
    minf = [[math.inf] * (C + 1) for _ in range(n + 1)]
    pq = [(0, 1, 0, 0)]
    while pq:
        d, u, f, c = heapq.heappop(pq)
        if d > dist[(u, f, c)] or any(f >= minf[u][j] for j in range(c + 1)):
            continue
        minf[u][c] = f
        if u == n:
            path, s = [], (u, f, c)
            while s in par:
                s, i, used = par[s]
                path.append((i, used))
            return d, path[::-1]
        if f == K + 1:
            continue
        for v, p, i in adj[u]:
            for nc, cost in ((c, p), (c + 1, p // 2))[:2 if c < C else 1]:
                s, nd = (v, f + 1, nc), d + cost
                if nd < dist.get(s, math.inf):
                    dist[s], par[s] = nd, ((u, f, c), i, nc > c)
                    heapq.heappush(pq, (nd, v, f + 1, nc))
    return -1, []


def bellman_ford(n, E, K, C):
    d = [[math.inf] * (C + 1) for _ in range(n + 1)]
    d[1][0] = 0
    for _ in range(K + 1):
        nd = [r[:] for r in d]
        for u, v, p in E:
            for c in range(C + 1):
                if d[u][c] < math.inf:
                    nd[v][c] = min(nd[v][c], d[u][c] + p)
                    if c < C:
                        nd[v][c + 1] = min(nd[v][c + 1], d[u][c] + p // 2)
        d = nd
    m = min(d[n])
    return -1 if m == math.inf else m


def generate(n, m, K, seed):
    r = random.Random(seed)
    route = [1] + r.sample(range(2, n), r.randint(0, min(K, n - 2))) + [n] if n > 1 else [1]
    E = [(a, b, r.randint(50, 500)) for a, b in zip(route, route[1:])]
    seen = {(a, b) for a, b, _ in E}
    m = min(max(m, len(E)), n * (n - 1))
    while len(E) < m:
        a, b = r.randint(1, n), r.randint(1, n)
        if a != b and (a, b) not in seen:
            seen.add((a, b))
            E.append((a, b, r.randint(50, 500)))
    return E


def read_csv(path):
    E = []
    with open(path, newline="") as f:
        for row in csv.reader(f):
            try:
                E.append(tuple(int(x) for x in row[:3]))
            except ValueError:
                continue
    if not E or any(len(e) != 3 for e in E):
        sys.exit("CSV needs rows of: from, to, price")
    return max(max(u, v) for u, v, _ in E), E


def write_csv(path, E, route):
    on = dict(route)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["From", "To", "Price", "On path", "Coupon used", "Paid"])
        for i, (u, v, p) in enumerate(E):
            w.writerow([u, v, p, "x" if i in on else "", "x" if on.get(i) else "", (p // 2 if on[i] else p) if i in on else ""])


def draw(ax, n, E, route, step):
    from matplotlib.patches import FancyArrowPatch
    mid = list(range(2, n))
    pos = {c: (math.cos(math.pi / 2 - 2 * math.pi * (j + 0.5) / len(mid)), math.sin(math.pi / 2 - 2 * math.pi * (j + 0.5) / len(mid))) for j, c in enumerate(mid)}
    pos[1], pos[n] = (-1.45, 0), (1.45, 0)
    on = {i: (k, used) for k, (i, used) in enumerate(route)}
    stops = {E[i][1] for i, _ in route[:-1]}
    here = E[route[step - 1][0]][1] if step else 1
    count = {}
    ax.clear()
    for i, (u, v, p) in enumerate(E):
        if u == v:
            continue
        count[(u, v)] = count.get((u, v), -1) + 1
        rad = 0.15 + 0.12 * count[(u, v)]
        k, used = on.get(i, (None, False))
        done = k is not None and k < step
        colour = ("#e0a800" if used else "#1c6dd0") if done else "#b5b9c0"
        ax.add_patch(FancyArrowPatch(pos[u], pos[v], arrowstyle="-|>", mutation_scale=16 if done else 11, lw=3.2 if done else 0.9,
                                     color=colour, connectionstyle=f"arc3,rad={rad}", shrinkA=17, shrinkB=17, zorder=3 if done else 1))
        (x1, y1), (x2, y2) = pos[u], pos[v]
        lx, ly = (x1 + x2) / 2 + 0.5 * rad * (y2 - y1), (y1 + y2) / 2 - 0.5 * rad * (x2 - x1)
        text = f"{p} → {p // 2}" if done and used else str(p)
        ax.text(lx, ly, text, fontsize=9 if done else 7.5, ha="center", va="center", fontweight="bold" if done else "normal", zorder=4,
                color="#7a5c00" if done and used else "#1d2321" if done else "#555b63", bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    for c, (x, y) in pos.items():
        fill = "#2f9e44" if c == 1 else "#e03131" if c == n else "#f08c00" if c in stops else "#dde3ea"
        ax.scatter(x, y, s=620, color=fill, edgecolors="black", linewidths=3 if c == here else 1, zorder=5)
        ax.text(x, y, str(c), ha="center", va="center", fontsize=11, fontweight="bold", color="white" if c in (1, n) else "black", zorder=6)
    ax.set_xlim(-1.65, 1.65)
    ax.set_ylim(-1.25, 1.25)
    ax.set_aspect("equal")
    ax.axis("off")


def legend(ax):
    from matplotlib.lines import Line2D
    items = [("#2f9e44", "o", "Start (city 1)"), ("#e03131", "o", "Destination (city N)"), ("#f08c00", "o", "Intermediate stop"),
             ("#1c6dd0", "-", "Flight on chosen path"), ("#e0a800", "-", "Flight with coupon (price → discounted)"), ("#b5b9c0", "-", "Other flight")]
    ax.legend(handles=[Line2D([], [], color=c, marker=m if m == "o" else None, ls="-" if m == "-" else "", lw=3, ms=11) for c, m, _ in items],
              labels=[t for _, _, t in items], loc="upper center", bbox_to_anchor=(0.5, 0.02), ncol=3, fontsize=9, frameon=False)


def visualise(n, E, cost, route, K, C):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter
    fig, ax = plt.subplots(figsize=(11, 8.5))
    draw(ax, n, E, route, len(route))
    legend(ax)
    used = sum(u for _, u in route)
    ax.set_title(f"Cheapest route from 1 to {n}: cost {cost}, {max(len(route) - 1, 0)} stops (max {K}), {used} of {C} coupons" if cost >= 0 else f"No route from 1 to {n} within {K} stops", fontsize=12)
    fig.tight_layout()
    fig.savefig("route.png", dpi=150)
    if cost < 0 or not route:
        plt.close(fig)
        return

    def frame(k):
        s = min(k, len(route))
        draw(ax, n, E, route, s)
        legend(ax)
        spent = sum(E[i][2] // 2 if u else E[i][2] for i, u in route[:s])
        coupons = sum(u for _, u in route[:s])
        if s == 0:
            head = "Start at city 1"
        else:
            i, u = route[s - 1]
            a, b, p = E[i]
            head = f"Flight {s}: {a} → {b}, " + (f"coupon applied, {p} → {p // 2}" if u else f"price {p}")
        ax.set_title(f"{head}\nRunning cost {spent}   |   stops used {max(s - 1, 0)} of {K}   |   coupons used {coupons} of {C}", fontsize=12)
        fig.tight_layout()

    FuncAnimation(fig, frame, frames=len(route) + 3).save("journey.gif", writer=PillowWriter(fps=0.8))
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    ap.add_argument("--generate", nargs=2, type=int, metavar=("N", "M"))
    ap.add_argument("--seed", type=int)
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--no-plot", action="store_true")
    a = ap.parse_args()
    t = sys.stdin.read().split()
    try:
        if a.csv:
            K, C = int(t[0]), int(t[1])
            n, E = read_csv(a.csv)
        elif a.generate:
            K, C = int(t[0]), int(t[1])
            n = a.generate[0]
            if n < 1:
                sys.exit("N must be at least 1")
            E = generate(n, a.generate[1], K, a.seed)
            with open("generated_graph.csv", "w", newline="") as f:
                csv.writer(f).writerows([["From", "To", "Price"]] + E)
        else:
            n, m, K, C = map(int, t[:4])
            if len(t) < 4 + 3 * m:
                sys.exit(f"Expected {m} flights, got {(len(t) - 4) // 3}")
            E = [tuple(map(int, t[4 + 3 * i:7 + 3 * i])) for i in range(m)]
    except (IndexError, ValueError):
        sys.exit("Input must be 'N M', 'K C' and then M lines 'u v p' (or 'K C' with --csv / --generate)")
    if n < 1 or K < 0 or C < 0:
        sys.exit("Need N >= 1, K >= 0 and C >= 0")
    for u, v, p in E:
        if not (1 <= u <= n and 1 <= v <= n) or p < 0:
            sys.exit(f"Invalid flight {u} {v} {p}")
    t0 = time.perf_counter()
    cost, route = dijkstra(n, E, K, C)
    td = time.perf_counter() - t0
    print(cost)
    for i, used in route:
        u, v, p = E[i]
        print(f"{u} -> {v}: {p // 2} (coupon, {p} -> {p // 2})" if used else f"{u} -> {v}: {p}")
    if cost >= 0:
        print(f"Flights: {len(route)}, stops: {max(len(route) - 1, 0)}, coupons used: {sum(u for _, u in route)}")
    write_csv("flights_path.csv", E, route)
    if a.compare:
        t0 = time.perf_counter()
        bf = bellman_ford(n, E, K, C)
        print(f"Dijkstra: {cost} in {td * 1000:.3f} ms, Bellman-Ford: {bf} in {(time.perf_counter() - t0) * 1000:.3f} ms")
    if not a.no_plot and n <= 40:
        try:
            visualise(n, E, cost, route, K, C)
        except ImportError:
            pass


if __name__ == "__main__":
    main()
