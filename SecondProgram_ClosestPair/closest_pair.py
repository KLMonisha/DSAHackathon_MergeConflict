import sys
import math
import time
import random
import argparse


def d2(p, q):
    dx = p[0] - q[0]
    dy = p[1] - q[1]
    return dx * dx + dy * dy


def brute_force(P):
    n = len(P)
    best = math.inf
    pair = None
    for i in range(n):
        xi, yi = P[i]
        for j in range(i + 1, n):
            dx = xi - P[j][0]
            dy = yi - P[j][1]
            d = dx * dx + dy * dy
            if d < best:
                best = d
                pair = (i, j)
    return best, pair


def divide_and_conquer(P, trace=None):
    n = len(P)
    info = {"top": None, "depth": 0}
    if n < 2:
        return math.inf, None, info
    X = sorted(range(n), key=lambda i: (P[i][0], P[i][1]))
    Y = sorted(range(n), key=lambda i: (P[i][1], P[i][0]))
    left = [False] * n

    def solve(X, Y, depth):
        info["depth"] = max(info["depth"], depth)
        m = len(X)
        if m <= 3:
            best = math.inf
            pair = None
            for a in range(m):
                for b in range(a + 1, m):
                    d = d2(P[X[a]], P[X[b]])
                    if d < best:
                        best = d
                        pair = (X[a], X[b])
            if trace is not None:
                trace.append(("base", depth, P[X[0]][0], P[X[-1]][0], None, X, best, pair, [], []))
            return best, pair
        h = m // 2
        midx = P[X[h]][0]
        L = X[:h]
        R = X[h:]
        for i in L:
            left[i] = True
        YL = [i for i in Y if left[i]]
        YR = [i for i in Y if not left[i]]
        for i in L:
            left[i] = False
        if trace is not None:
            trace.append(("split", depth, P[X[0]][0], P[X[-1]][0], midx, X, None, None, [], []))
        bl = solve(L, YL, depth + 1)
        br = solve(R, YR, depth + 1)
        best, pair = bl if bl[0] <= br[0] else br
        delta = best
        S = [i for i in Y if (P[i][0] - midx) ** 2 < best]
        checked = []
        for a in range(len(S)):
            pa = P[S[a]]
            for b in range(a + 1, len(S)):
                pb = P[S[b]]
                dy = pb[1] - pa[1]
                if dy * dy >= best:
                    break
                d = d2(pa, pb)
                if trace is not None:
                    checked.append((S[a], S[b]))
                if d < best:
                    best = d
                    pair = (S[a], S[b])
        if depth == 0:
            info["top"] = (midx, math.sqrt(delta), len(S))
        if trace is not None:
            trace.append(("merge", depth, P[X[0]][0], P[X[-1]][0], midx, X, best, pair, S, checked, math.sqrt(delta)))
        return best, pair

    best, pair = solve(X, Y, 0)
    return best, pair, info


def generate(n, use_float=False, limit=1000, seed=None):
    rnd = random.Random(seed)
    if use_float:
        return [(round(rnd.uniform(-limit, limit), 2), round(rnd.uniform(-limit, limit), 2)) for _ in range(n)]
    limit = int(limit)
    return [(rnd.randint(-limit, limit), rnd.randint(-limit, limit)) for _ in range(n)]


def num(s):
    try:
        return int(s)
    except ValueError:
        return float(s)


def fmt(v):
    if isinstance(v, int):
        return str(v)
    s = ("%.6f" % v).rstrip("0").rstrip(".")
    return "0" if s == "-0" else s


def pt(p):
    return "(" + fmt(p[0]) + ", " + fmt(p[1]) + ")"


def line(name, P, best, pair):
    if pair is None:
        return name + ": no pair exists (N < 2)"
    a, b = sorted((P[pair[0]], P[pair[1]]))
    return name + ": " + "%.6f" % math.sqrt(best) + " " + pt(a) + " " + pt(b)


def run(P):
    t0 = time.perf_counter()
    bf = brute_force(P)
    t1 = time.perf_counter()
    dc = divide_and_conquer(P)
    t2 = time.perf_counter()
    return bf, dc, (t1 - t0) * 1000, (t2 - t1) * 1000


def plot_plane(P, bf, dc, show):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 7))
    if P:
        ax.scatter([p[0] for p in P], [p[1] for p in P], s=14, color="#333333", zorder=3, label="Points")
    top = dc[2]["top"]
    if top:
        midx, d, k = top
        ax.axvspan(midx - d, midx + d, color="#f2c94c", alpha=0.3, zorder=1, label="Strip of width 2d (d = %.4f, %d points)" % (d, k))
        ax.axvline(midx, color="#7b3fc4", ls="--", lw=1.6, zorder=2, label="Dividing line x = %s" % fmt(midx))
    if bf[1]:
        a, b = P[bf[1][0]], P[bf[1][1]]
        ax.plot([a[0], b[0]], [a[1], b[1]], color="#d9480f", lw=3, marker="o", ms=9, mfc="none", mew=2, zorder=4, label="Brute force pair, d = %.6f" % math.sqrt(bf[0]))
    if dc[1]:
        a, b = P[dc[1][0]], P[dc[1][1]]
        ax.plot([a[0], b[0]], [a[1], b[1]], color="#1c6dd0", lw=2, ls="--", marker="s", ms=13, mfc="none", mew=1.8, zorder=5, label="Divide and conquer pair, d = %.6f" % math.sqrt(dc[0]))
        for p, off in ((a, 12), (b, -16)):
            ax.annotate(pt(p), p, textcoords="offset points", xytext=(10, off), fontsize=9, zorder=6)
    if len(P) < 2:
        ax.text(0.5, 0.5, "N = %d, no pair exists" % len(P), transform=ax.transAxes, ha="center", fontsize=14)
    ax.set_title("Closest pair of points, N = %d" % len(P))
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=9)
    fig.tight_layout()
    fig.savefig("closest_pair_plane.png", dpi=150)
    if show:
        plt.show()
    plt.close(fig)


def benchmark(use_float, limit, seed, show):
    sizes = [100, 200, 400, 800, 1600, 3200, 6400]
    rows = []
    print("N\tBrute-Force(ms)\tDivide-and-Conquer(ms)\tAgree")
    for n in sizes:
        P = generate(n, use_float, max(limit, n * 10), None if seed is None else seed + n)
        bf, dc, tb, td = run(P)
        ok = abs(math.sqrt(bf[0]) - math.sqrt(dc[0])) < 1e-9
        rows.append((n, tb, td, ok))
        print("%d\t%.3f\t%.3f\t%s" % (n, tb, td, "yes" if ok else "NO"))
    good = 0
    total = 2000
    rnd = random.Random(seed)
    for t in range(total):
        n = rnd.randint(2, 60)
        lim = rnd.choice([1, 3, 10, 100])
        kind = t % 5
        if kind == 0:
            P = [(rnd.randint(0, lim), rnd.randint(0, lim)) for _ in range(n)]
        elif kind == 1:
            c = rnd.randint(-5, 5)
            P = [(c, rnd.randint(-lim, lim)) for _ in range(n)]
        elif kind == 2:
            c = rnd.randint(-5, 5)
            P = [(rnd.randint(-lim, lim), c) for _ in range(n)]
        elif kind == 3:
            P = [(v, 2 * v + 1) for v in (rnd.randint(-lim, lim) for _ in range(n))]
        else:
            P = [(round(rnd.uniform(-lim, lim), 2), round(rnd.uniform(-lim, lim), 2)) for _ in range(n)]
        if brute_force(P)[0] == divide_and_conquer(P)[0]:
            good += 1
    print("Agreement: %d/%d random tests gave the same minimum distance" % (good, total))
    import matplotlib.pyplot as plt
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5))
    ns = [r[0] for r in rows]
    for ax, log in ((a1, False), (a2, True)):
        ax.plot(ns, [r[1] for r in rows], color="#d9480f", marker="o", lw=2, label="Brute force O(n^2)")
        ax.plot(ns, [r[2] for r in rows], color="#1c6dd0", marker="s", ls="--", lw=2, label="Divide and conquer O(n log n)")
        ax.set_xlabel("N")
        ax.set_ylabel("Time (ms)")
        ax.grid(alpha=0.3)
        ax.legend()
        if log:
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.set_title("Running time vs N (log-log)")
        else:
            ax.set_title("Running time vs N")
    fig.tight_layout()
    fig.savefig("runtime_vs_n.png", dpi=150)
    if show:
        plt.show()
    plt.close(fig)


def animate(P, show):
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter
    if len(P) < 2 or len(P) > 300:
        print("Animation skipped: needs 2 <= N <= 300")
        return
    trace = []
    divide_and_conquer(P, trace)
    xs = [p[0] for p in P]
    ys = [p[1] for p in P]
    pad = max(max(xs) - min(xs), max(ys) - min(ys), 1) * 0.05
    fig, ax = plt.subplots(figsize=(8, 6.5))

    def draw(k):
        ax.clear()
        kind, depth, x0, x1, midx, ids, best, pair, S, checked = trace[k][:10]
        inside = set(ids)
        ax.set_xlim(min(xs) - pad, max(xs) + pad)
        ax.set_ylim(min(ys) - pad, max(ys) + pad)
        ax.axvspan(x0, x1 if x1 > x0 else x0 + pad * 0.05, color="#1c6dd0", alpha=0.08)
        ax.scatter([p[0] for i, p in enumerate(P) if i not in inside], [p[1] for i, p in enumerate(P) if i not in inside], s=12, color="#cccccc")
        ax.scatter([P[i][0] for i in ids], [P[i][1] for i in ids], s=16, color="#333333", zorder=3)
        if kind == "split":
            ax.axvline(midx, color="#7b3fc4", ls="--", lw=1.6)
            text = "Split %d points at x = %s (depth %d)" % (len(ids), fmt(midx), depth)
        elif kind == "base":
            text = "Base case: %d points checked directly, d = %.4f" % (len(ids), math.sqrt(best))
        else:
            d = trace[k][10]
            ax.axvline(midx, color="#7b3fc4", ls="--", lw=1.6)
            ax.axvspan(midx - d, midx + d, color="#f2c94c", alpha=0.3)
            for a, b in checked:
                ax.plot([P[a][0], P[b][0]], [P[a][1], P[b][1]], color="#999999", lw=0.8)
            ax.scatter([P[i][0] for i in S], [P[i][1] for i in S], s=60, facecolors="none", edgecolors="#c99a12", zorder=4)
            text = "Merge at x = %s: d = %.4f, %d points in strip, best now %.4f" % (fmt(midx), d, len(S), math.sqrt(best))
        if pair:
            a, b = P[pair[0]], P[pair[1]]
            ax.plot([a[0], b[0]], [a[1], b[1]], color="#1c6dd0", lw=2.5, ls="--", zorder=5)
        ax.set_title("Step %d/%d  %s" % (k + 1, len(trace), text), fontsize=10)
        ax.grid(alpha=0.25)

    anim = FuncAnimation(fig, draw, frames=len(trace), interval=700)
    anim.save("dnc_animation.gif", writer=PillowWriter(fps=2))
    if show:
        plt.show()
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--float", action="store_true")
    ap.add_argument("--range", type=float, default=1000)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--bench", action="store_true")
    ap.add_argument("--animate", action="store_true")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--no-plot", action="store_true")
    args = ap.parse_args()
    data = sys.stdin.read().split()
    if not data:
        print("Input N on standard input")
        return
    n = int(data[0])
    if n < 0:
        print("N cannot be negative")
        return
    if len(data) >= 1 + 2 * n and n > 0:
        P = [(num(data[1 + 2 * i]), num(data[2 + 2 * i])) for i in range(n)]
    else:
        P = generate(n, args.float, args.range, args.seed)
    bf, dc, tb, td = run(P)
    print(line("Brute-Force", P, bf[0], bf[1]))
    print(line("Divide-and-Conquer", P, dc[0], dc[1]))
    print("Time: Brute-Force %.3f ms, Divide-and-Conquer %.3f ms" % (tb, td))
    if args.no_plot:
        return
    try:
        import matplotlib
        if not args.show:
            matplotlib.use("Agg")
    except ImportError:
        return
    plot_plane(P, bf, dc, args.show)
    if args.bench:
        benchmark(args.float, args.range, args.seed, args.show)
    if args.animate:
        animate(P, args.show)


if __name__ == "__main__":
    main()
