import java.util.*;
import java.io.*;

public class Main {
    public static void main(String[] args) throws Exception {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));

        int T = Integer.parseInt(br.readLine().trim());
        int n = Integer.parseInt(br.readLine().trim());

        char[][] grid = new char[n][n];

        for (int i = 0; i < n; i++) {
            String line = br.readLine().trim();

            if (line.contains(",")) {
                String[] cells = line.split("\\s*,\\s*");
                for (int j = 0; j < n; j++) {
                    grid[i][j] = cells[j].charAt(0);
                }
            } else {
                for (int j = 0; j < n; j++) {
                    grid[i][j] = line.charAt(j);
                }
            }
        }

        int answer = shortestPath(grid, T);
        System.out.println(answer);
    }

    static int shortestPath(char[][] grid, int T) throws IOException {
        int n = grid.length;
        int sr = 0, sc = 0;
        int target = 0;

        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                char ch = grid[i][j];

                if (ch == 'S') {
                    sr = i;
                    sc = j;
                }

                if (ch >= 'a' && ch < 'a' + T) {
                    target |= 1 << (ch - 'a');
                }
            }
        }

        boolean[][][] visited = new boolean[n][n][64];
        int[][][] pr = new int[n][n][64];
        int[][][] pc = new int[n][n][64];
        int[][][] pm = new int[n][n][64];

        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                Arrays.fill(pr[i][j], -1);
                Arrays.fill(pc[i][j], -1);
                Arrays.fill(pm[i][j], -1);
            }
        }

        Queue<int[]> q = new LinkedList<>();
        q.offer(new int[]{sr, sc, 0, 0});
        visited[sr][sc][0] = true;

        int[] dr = {-1, 1, 0, 0};
        int[] dc = {0, 0, -1, 1};

        int er = -1, ec = -1, em = -1, distance = -1;

        while (!q.isEmpty()) {
            int[] cur = q.poll();

            int r = cur[0];
            int c = cur[1];
            int keys = cur[2];
            int steps = cur[3];

            if (grid[r][c] == 'E') {
                er = r;
                ec = c;
                em = keys;
                distance = steps;
                break;
            }

            for (int d = 0; d < 4; d++) {
                int nr = r + dr[d];
                int nc = c + dc[d];

                if (nr < 0 || nr >= n || nc < 0 || nc >= n)
                    continue;

                char ch = grid[nr][nc];

                if (ch == '#')
                    continue;

                if (ch >= 'A' && ch < 'A' + T &&
                    (keys & (1 << (ch - 'A'))) == 0)
                    continue;

                int newKeys = keys;

                if (ch >= 'a' && ch < 'a' + T)
                    newKeys |= 1 << (ch - 'a');

                if (!visited[nr][nc][newKeys]) {
                    visited[nr][nc][newKeys] = true;

                    pr[nr][nc][newKeys] = r;
                    pc[nr][nc][newKeys] = c;
                    pm[nr][nc][newKeys] = keys;

                    q.offer(new int[]{nr, nc, newKeys, steps + 1});
                }
            }
        }

        if (distance == -1)
            return -1;

        char[][] pathGrid = new char[n][n];

        for (int i = 0; i < n; i++)
            pathGrid[i] = grid[i].clone();

        int r = er, c = ec, mask = em;

        while (r != sr || c != sc || mask != 0) {
            if (pathGrid[r][c] == '.')
                pathGrid[r][c] = 'x';

            int nr = pr[r][c][mask];
            int nc = pc[r][c][mask];
            int nm = pm[r][c][mask];

            r = nr;
            c = nc;
            mask = nm;
        }

        try (PrintWriter out = new PrintWriter("shortest_path.csv")) {
            for (int i = 0; i < n; i++) {
                for (int j = 0; j < n; j++) {
                    if (j > 0)
                        out.print(",");
                    out.print(pathGrid[i][j]);
                }
                out.println();
            }
        }

        return distance;
    }
}