"""2-D magneto-quasistatic finite-volume solver for A_z (time harmonic).

    -div(nu grad A) + j w sigma A - sigma E_c = J_s            (per cell)
    sum over conductor c of sigma (-j w A + E_c) dS = I_c      (one row each)

Tensor-product grid, node unknowns, cell-wise nu, sigma and source.  Units SI
(lengths in metres).  Boundaries: 'dirichlet' sides hold A = 0, the rest are
natural (zero normal derivative of A = symmetry plane / flux tangential).

Materials are given as a function cell(xc, yc) -> dict(mur, cond, src)
  mur  : relative permeability
  cond : None or conductor id (solid, sigma = SIGMA, current constrained)
  src  : None or (group id, weight) - a homogenised stranded conductor; the
         group's current is spread uniformly over its weighted area.
Excitation: dict of currents (peak phasors) for solid conductors and source
groups.  Everything is linear, so solve() returns the field for one
excitation; loss_matrix() builds the Hermitian loss form from unit solves.
"""
import math
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl

MU0 = 4e-7 * math.pi


def axis(segments):
    """[(a, b, h)] -> sorted node coordinates, every a and b a node, spacing <= h."""
    pts = []
    for a, b, h in segments:
        n = max(1, int(math.ceil((b - a) / h - 1e-9)))
        pts.extend(np.linspace(a, b, n + 1))
    return np.unique(np.round(np.array(pts), 12))


class Model:
    def __init__(self, x, y, cell, sigma, dirichlet=('xmax', 'ymax'), sub=4):
        self.x, self.y = np.asarray(x), np.asarray(y)
        nx, ny = len(x) - 1, len(y) - 1
        self.hx, self.hy = np.diff(self.x), np.diff(self.y)
        self.nu = np.empty((nx, ny)); self.cond = np.full((nx, ny), -1, int)
        self.src = {}                 # group -> array of weights (area fraction) per cell
        self.sigma = sigma
        for i in range(nx):
            for j in range(ny):
                xc = 0.5 * (x[i] + x[i + 1]); yc = 0.5 * (y[j] + y[j + 1])
                m = cell(xc, yc)
                self.nu[i, j] = 1.0 / (MU0 * m.get('mur', 1.0))
                if m.get('cond') is not None:
                    self.cond[i, j] = m['cond']
                # stranded groups: sub-sample the cell for the area fraction
                for g in m.get('near', ()):  # groups whose shape may cut this cell
                    f = 0.0
                    for a in range(sub):
                        for b in range(sub):
                            xs = x[i] + (a + 0.5) / sub * self.hx[i]
                            ys = y[j] + (b + 0.5) / sub * self.hy[j]
                            if g[1](xs, ys):
                                f += 1.0
                    f /= sub * sub
                    if f > 0:
                        self.src.setdefault(g[0], np.zeros((nx, ny)))[i, j] += f
        self.conds = sorted(set(self.cond[self.cond >= 0].ravel().tolist()))
        self.dirichlet = dirichlet
        self._assemble_static()

    # ------------------------------------------------------------ assembly
    def _assemble_static(self):
        x, y, hx, hy, nu = self.x, self.y, self.hx, self.hy, self.nu
        NX, NY = len(x), len(y)
        idx = lambda i, j: i + j * NX
        rows, cols, vals = [], [], []
        # cell-wise area quarters to nodes: sigma area and source mapping
        ncell_x, ncell_y = NX - 1, NY - 1

        def c_nu(i, j):
            if 0 <= i < ncell_x and 0 <= j < ncell_y:
                return nu[i, j]
            return 0.0

        def h_x(i):
            return hx[i] if 0 <= i < ncell_x else 0.0

        def h_y(j):
            return hy[j] if 0 <= j < ncell_y else 0.0
        diag = np.zeros(NX * NY)
        for j in range(NY):
            for i in range(NX):
                p = idx(i, j)
                if i + 1 < NX:
                    ce = (c_nu(i, j - 1) * h_y(j - 1) + c_nu(i, j) * h_y(j)) / 2 / hx[i]
                    rows.append(p); cols.append(idx(i + 1, j)); vals.append(-ce); diag[p] += ce
                if i - 1 >= 0:
                    cw = (c_nu(i - 1, j - 1) * h_y(j - 1) + c_nu(i - 1, j) * h_y(j)) / 2 / hx[i - 1]
                    rows.append(p); cols.append(idx(i - 1, j)); vals.append(-cw); diag[p] += cw
                if j + 1 < NY:
                    cn = (c_nu(i - 1, j) * h_x(i - 1) + c_nu(i, j) * h_x(i)) / 2 / hy[j]
                    rows.append(p); cols.append(idx(i, j + 1)); vals.append(-cn); diag[p] += cn
                if j - 1 >= 0:
                    cs = (c_nu(i - 1, j - 1) * h_x(i - 1) + c_nu(i, j - 1) * h_x(i)) / 2 / hy[j - 1]
                    rows.append(p); cols.append(idx(i, j - 1)); vals.append(-cs); diag[p] += cs
        rows += list(range(NX * NY)); cols += list(range(NX * NY)); vals += list(diag)
        self.K = sp.csr_matrix((vals, (rows, cols)), shape=(NX * NY, NX * NY))
        # node weights: conductor sigma-area per conductor, source weights per group
        self.cellA = np.outer(hx, hy)
        self.node_cond = {}
        for c in self.conds:
            w = np.where(self.cond == c, self.cellA, 0.0)
            self.node_cond[c] = self._to_nodes(w)
        self.node_src = {g: self._to_nodes(f * self.cellA) for g, f in self.src.items()}
        self.src_area = {g: float((f * self.cellA).sum()) for g, f in self.src.items()}
        # boundary nodes
        fixed = np.zeros((NX, NY), bool)
        for side in self.dirichlet:
            if side == 'xmin': fixed[0, :] = True
            if side == 'xmax': fixed[-1, :] = True
            if side == 'ymin': fixed[:, 0] = True
            if side == 'ymax': fixed[:, -1] = True
        self.fixed = fixed.T.ravel()          # node order i + j*NX

    def _to_nodes(self, w):
        """cell quantity (per cell, e.g. area) -> quarter to each corner node, flattened."""
        NX, NY = len(self.x), len(self.y)
        n = np.zeros((NX, NY))
        q = w / 4.0
        n[:-1, :-1] += q; n[1:, :-1] += q; n[:-1, 1:] += q; n[1:, 1:] += q
        return n.T.ravel()

    # ------------------------------------------------------------ solve
    def solve(self, omega, currents, sigma=None):
        """currents: {conductor id or group id: peak phasor}.  -> (A nodes, E_c dict)"""
        sigma = self.sigma if sigma is None else sigma
        N = self.K.shape[0]; nc = len(self.conds)
        K = self.K.astype(complex).tolil() if False else self.K.astype(complex)
        extra_r, extra_c, extra_v = [], [], []
        rhs = np.zeros(N + nc, complex)
        diag_add = np.zeros(N, complex)
        for k, c in enumerate(self.conds):
            s = sigma * self.node_cond[c]            # sigma * area at nodes
            diag_add += 1j * omega * s
            nz = np.nonzero(s)[0]
            # -sigma E_c term in node rows (column N+k)
            extra_r += list(nz); extra_c += [N + k] * len(nz); extra_v += list(-s[nz])
            # constraint row: sum(-j w s A) + E_c sum(s) = I_c
            extra_r += [N + k] * len(nz); extra_c += list(nz); extra_v += list(-1j * omega * s[nz])
            extra_r.append(N + k); extra_c.append(N + k); extra_v.append(s.sum())
            rhs[N + k] = currents.get(c, 0.0)
        for g, w in self.node_src.items():
            I = currents.get(g, 0.0)
            if I:
                rhs[:N] += I * w / self.src_area[g]
        A = sp.bmat([[K + sp.diags(diag_add), None], [None, sp.csr_matrix((nc, nc))]], format='lil') if nc else (K + sp.diags(diag_add)).tolil()
        if nc:
            A = A.tocsr() + sp.csr_matrix((extra_v, (extra_r, extra_c)), shape=(N + nc, N + nc))
        A = A.tocsr()
        # Dirichlet: replace rows
        fx = np.nonzero(self.fixed)[0]
        if len(fx):
            A = A.tolil()
            for p in fx:
                A.rows[p] = [p]; A.data[p] = [1.0]
            A = A.tocsr(); rhs[fx] = 0.0
        sol = spl.spsolve(A.tocsc(), rhs)
        return sol[:N], {c: sol[N + k] for k, c in enumerate(self.conds)}

    # ------------------------------------------------------------ post
    def grid_A(self, a):
        return a.reshape(len(self.y), len(self.x)).T       # [i, j]

    def cell_B(self, a):
        """cell-centre (Bx, By) complex, from node A."""
        A = self.grid_A(a)
        dAdy = ((A[:-1, 1:] + A[1:, 1:]) - (A[:-1, :-1] + A[1:, :-1])) / 2 / self.hy[None, :]
        dAdx = ((A[1:, :-1] + A[1:, 1:]) - (A[:-1, :-1] + A[:-1, 1:])) / 2 / self.hx[:, None]
        return dAdy, -dAdx

    def solid_loss(self, a, E, omega, sigma=None, weight=None):
        """time-average loss per unit length [W/m] of the solid conductors, by conductor.
        weight: optional per-cell multiplier (e.g. local turn length / reference)."""
        sigma = self.sigma if sigma is None else sigma
        A = self.grid_A(a)
        Ac = (A[:-1, :-1] + A[1:, :-1] + A[:-1, 1:] + A[1:, 1:]) / 4
        out = {}
        for c in self.conds:
            m = self.cond == c
            Ecell = -1j * omega * Ac + E[c]
            dens = 0.5 * sigma * np.abs(Ecell) ** 2 * self.cellA
            if weight is not None:
                dens = dens * weight
            out[c] = float(dens[m].sum())
        return out

    def energy(self, a, currents_nodes=None):
        """magnetic energy per unit length, 1/2 int nu |B|^2 / 2 (peak phasors -> time average x2 = peak energy/2)."""
        bx, by = self.cell_B(a)
        return float(0.5 * (self.nu * (np.abs(bx) ** 2 + np.abs(by) ** 2) * self.cellA).sum())
