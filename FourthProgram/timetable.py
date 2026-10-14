import sys, csv, time, random, argparse


def adjacency(n, E):
    a = [set() for _ in range(n)]
    for u, v in E:
        a[u].add(v)
        a[v].add(u)
    return a


def valid(c, n, R, E):
    return len(c) == n and min(c) >= 0 and all(c[u] != c[v] for u, v in E) and max(c.count(s) for s in set(c)) <= R


def dsatur(n, R, a):
    c, size, sat = [-1] * n, [], [set() for _ in range(n)]
    for _ in range(n):
        u = max((v for v in range(n) if c[v] < 0), key=lambda v: (len(sat[v]), len(a[v]), -v))
        s = next((s for s in range(len(size)) if s not in sat[u] and size[s] < R), len(size))
        if s == len(size):
            size.append(0)
        c[u] = s
        size[s] += 1
        for v in a[u]:
            sat[v].add(s)
    return c


def lower_bound(n, R, a):
    best = 1
    for order in (sorted(range(n), key=lambda u: -len(a[u])), sorted(range(n), key=lambda u: len(a[u])), range(n), range(n - 1, -1, -1)):
        q = []
        for u in order:
            if all(v in a[u] for v in q):
                q.append(u)
        best = max(best, len(q))
    return max(best, -(-n // R))


def branch_and_bound(n, R, a, greedy, limit):
    end = time.perf_counter() + limit
    best, lb, st = greedy[:], lower_bound(n, R, a), {"nodes": 0, "out": False}

    def feasible(k):
        c, size, cnt, sat = [-1] * n, [0] * k, [[0] * k for _ in range(n)], [0] * n

        def go(done):
            st["nodes"] += 1
            if time.perf_counter() > end:
                st["out"] = True
                return False
            if done == n:
                return True
            u = max((v for v in range(n) if c[v] < 0), key=lambda v: (sat[v], len(a[v])))
            empty_tried = False
            for s in range(k):
                if cnt[u][s] or size[s] >= R or (size[s] == 0 and empty_tried):
                    continue
                empty_tried |= size[s] == 0
                c[u] = s
                size[s] += 1
                for v in a[u]:
                    sat[v] += cnt[v][s] == 0
                    cnt[v][s] += 1
                if go(done + 1):
                    return True
                for v in a[u]:
                    cnt[v][s] -= 1
                    sat[v] -= cnt[v][s] == 0
                c[u] = -1
                size[s] -= 1
                if st["out"]:
                    return False
            return False

        return c if go(0) else None

    k = max(best)
    while k >= lb:
        c = feasible(k)
        if c is None:
            break
        best, k = c, max(c)
    return best, not st["out"], st["nodes"], lb


def groups(c):
    g = {}
    for i, s in enumerate(c):
        g.setdefault(s, []).append(i + 1)
    return [g[s] for s in sorted(g)]


def write_csv(path, c, R):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Slot"] + [f"Hall {i + 1}" for i in range(R)])
        for i, g in enumerate(groups(c)):
            w.writerow([i + 1] + g + [""] * (R - len(g)))


def solve(n, R, E, limit):
    a = adjacency(n, E)
    t = time.perf_counter()
    g = dsatur(n, R, a)
    tg = time.perf_counter() - t
    t = time.perf_counter()
    e, opt, nodes, lb = branch_and_bound(n, R, a, g, limit)
    te = time.perf_counter() - t
    assert valid(g, n, R, E) and valid(e, n, R, E)
    return g, tg, e, te, opt, nodes, lb


def random_graph(n, d, seed):
    r = random.Random(seed)
    return {(u, v) for u in range(n) for v in range(u + 1, n) if r.random() < d}


def colours(k):
    import matplotlib.pyplot as plt
    cm = plt.get_cmap("tab10" if k <= 10 else "tab20")
    return [cm(i % cm.N) for i in range(k)]


def draw(n, E, c, R):
    import math
    import matplotlib.pyplot as plt
    k = max(c) + 1
    col = colours(k)
    fig, (g1, g2) = plt.subplots(1, 2, figsize=(14, 6.5), gridspec_kw={"width_ratios": [1.1, 1]})
    pos = [(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)) for i in range(n)]
    for u, v in E:
        g1.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]], color="#999999", lw=0.7, zorder=1)
    for i, (x, y) in enumerate(pos):
        g1.scatter(x, y, s=max(80, 600 - 8 * n), color=col[c[i]], edgecolors="black", zorder=2)
        if n <= 60:
            g1.text(x, y, str(i + 1), ha="center", va="center", fontsize=8 if n > 30 else 10, zorder=3)
    g1.set_title(f"Conflict graph, {n} courses, {len(E)} conflicts, coloured by slot")
    g1.set_aspect("equal")
    g1.axis("off")
    for r, row in enumerate(groups(c)):
        for h in range(R if R <= 30 else len(row)):
            g2.add_patch(plt.Rectangle((h, k - r - 1), 1, 1, facecolor=col[r] if h < len(row) else "white", edgecolor="black"))
            if h < len(row):
                g2.text(h + 0.5, k - r - 0.5, str(row[h]), ha="center", va="center", fontsize=9)
    width = R if R <= 30 else max(len(r) for r in groups(c))
    g2.set_xlim(0, width)
    g2.set_ylim(0, k)
    g2.set_xticks([h + 0.5 for h in range(width)], [f"Hall {h + 1}" for h in range(width)], rotation=90 if width > 10 else 0)
    g2.set_yticks([k - r - 0.5 for r in range(k)], [f"Slot {r + 1}" for r in range(k)])
    g2.set_title(f"Timetable, {k} slots, at most {R} exams per slot")
    fig.tight_layout()
    fig.savefig("timetable.png", dpi=150)
    plt.close(fig)


def benchmark(R, d, limit, plot):
    rows = []
    print("N\tDSatur slots\tDSatur time(s)\tB&B slots\tB&B time(s)\tB&B proven optimal")
    for n in range(10, 61, 5):
        E = random_graph(n, d, 1000 + n)
        g, tg, e, te, opt, nodes, lb = solve(n, R, E, limit)
        rows.append((n, max(g) + 1, tg, max(e) + 1, te, opt))
        print("%d\t%d\t%.6f\t%d\t%.6f\t%s" % rows[-1])
    with open("benchmark.csv", "w", newline="") as f:
        csv.writer(f).writerows([["N", "dsatur_slots", "dsatur_seconds", "bnb_slots", "bnb_seconds", "bnb_optimal"]] + rows)
    if plot:
        import matplotlib.pyplot as plt
        fig, (p1, p2) = plt.subplots(1, 2, figsize=(13, 5))
        ns = [r[0] for r in rows]
        p1.plot(ns, [r[1] for r in rows], "o-", color="#d9480f", label="DSatur (greedy)")
        p1.plot(ns, [r[3] for r in rows], "s--", color="#1c6dd0", label="Branch and bound (exact)")
        p1.set(xlabel="N", ylabel="Slots used", title=f"Slots used vs N (density {d}, R = {R})")
        p2.plot(ns, [r[2] for r in rows], "o-", color="#d9480f", label="DSatur (greedy)")
        p2.plot(ns, [r[4] for r in rows], "s--", color="#1c6dd0", label="Branch and bound (exact)")
        p2.set(xlabel="N", ylabel="Time (s, log scale)", yscale="log", title=f"Running time vs N (time limit {limit}s)")
        for p in (p1, p2):
            p.grid(alpha=0.3)
            p.legend()
        fig.tight_layout()
        fig.savefig("comparison.png", dpi=150)
        plt.close(fig)


def read_input():
    lines = [l.split() for l in sys.stdin.read().splitlines() if l.strip()]
    if not lines or len(lines[0]) not in (2, 3):
        sys.exit("First line must be 'N M R' or 'N R'")
    if len(lines[0]) == 3:
        n, m, R = map(int, lines[0])
        if n < 1 or m < 0 or R < 1 or len(lines) < m + 1:
            sys.exit("Need N >= 1, M >= 0, R >= 1 and M edge lines")
        E = set()
        for l in lines[1:m + 1]:
            u, v = int(l[0]), int(l[1])
            if not (1 <= u <= n and 1 <= v <= n) or u == v:
                sys.exit(f"Invalid conflict {u} {v}")
            E.add((min(u, v) - 1, max(u, v) - 1))
        return n, R, E, 0.3
    n, R = map(int, lines[0])
    d = float(lines[1][0]) if len(lines) > 1 else 0.3
    seed = int(lines[1][1]) if len(lines) > 1 and len(lines[1]) > 1 else 42
    if n < 1 or R < 1 or not 0 <= d <= 1:
        sys.exit("Need N >= 1, R >= 1 and density between 0 and 1")
    return n, R, random_graph(n, d, seed), d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--time", type=float, default=30)
    ap.add_argument("--bench", action="store_true")
    ap.add_argument("--no-plot", action="store_true")
    args = ap.parse_args()
    n, R, E, d = read_input()
    sys.setrecursionlimit(max(1000, 2 * n + 100))
    g, tg, e, te, opt, nodes, lb = solve(n, R, E, args.time)
    gk, ek = max(g) + 1, max(e) + 1
    print(f"N = {n}, conflicts = {len(E)}, R = {R}, lower bound = {lb}")
    print(f"DSatur: {gk} slots, proven optimal: {'yes' if gk == lb or (opt and gk == ek) else 'no'}, time {tg:.6f} s")
    print(f"Branch and bound: {ek} slots, proven optimal: {'yes' if opt else 'no, time limit reached'}, time {te:.6f} s, nodes {nodes}")
    for name, c in (("DSatur", g), ("Branch and bound", e)):
        print(f"\n{name} timetable:")
        for i, grp in enumerate(groups(c)):
            print(f"Slot {i + 1}: " + ", ".join(map(str, grp)))
    write_csv("dsatur_timetable.csv", g, R)
    write_csv("exact_timetable.csv", e, R)
    plot = not args.no_plot
    if plot:
        try:
            import matplotlib
            matplotlib.use("Agg")
            draw(n, E, e, R)
        except ImportError:
            plot = False
    if args.bench:
        print()
        benchmark(R, d, min(args.time, 10), plot)


if __name__ == "__main__":
    main()
