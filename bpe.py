import warnings
import numpy as np


def vec(S):
    """Per scs definition, preserves inner product

    tr(A @ B) = vec(A) @ vec(B)
    https://www.cvxgrp.org/scs/api/cones.html#sdcone
    """
    j, i = np.triu_indices(S.shape[-1])
    scale = np.where(i == j, 1.0, np.sqrt(2))
    return S[..., i, j] * scale


def mat(s, n=None):
    """Inverse of vec() operation"""
    if n is None:
        l = s.shape[-1]
        n = int(0.5 * (np.sqrt(1 + 8 * l) - 1))
    S = np.empty(s.shape[:-1] + (n, n))
    j, i = np.triu_indices(n)
    scaled = np.where(i == j, 1.0, np.sqrt(0.5)) * s
    S[..., i, j] = scaled
    S[..., j, i] = scaled
    return S


class BasisPointExpansion:
    def __init__(self, n_coef):
        self._n = n_coef
        self._points = []
        self._yields = []
        self._errors = []
        self._M = None

    @property
    def n(self):
        return self._n

    def add_point(self, coef, yields, errors):
        if not all(isinstance(x, np.ndarray) for x in (coef, yields, errors)):
            raise ValueError("Wrong input type")
        if coef.shape != (self.n,):
            raise ValueError("coef has wrong shape")
        if yields.shape != errors.shape or len(yields.shape) != 1:
            raise ValueError("yields or errors has wrong shape")
        if np.any(yields < 0.0):
            raise ValueError("some yields are less than zero")
        if np.any(errors == 0.0):
            raise ValueError("some errors are zero")
        if self._yields and self._yields[0].shape != yields.shape:
            raise ValueError("yields shape does not match that of other basis points")
        self._points.append(coef)
        self._yields.append(yields)
        self._errors.append(errors)
        self._M = None

    def solve(self, algo="svd", tol=1e-5):
        """Solve for expansion matrix

        Algo options:
            svd: Weighted least-squares fit
            svd_pos: Like svd but adjusts eigenvalues to be pos-def
            dcp: Use disciplined convex programming to find least-squares under pos-def constraint
        tol: Target for how far lowest eigenvalue is above zero
        """
        points = np.stack(self._points)
        npt, n = points.shape
        assert n == self._n
        if npt < n * (n - 1):
            raise RuntimeError("Not enough points for the dimension of the problem")
        yields = np.stack(self._yields).T
        weight = 1.0 / np.stack(self._errors).T
        nbin, _ = yields.shape
        if algo.startswith("svd"):
            C = vec(points[:, None, :] * points[:, :, None])[None] * weight[:, :, None]
            u, s, vh = np.linalg.svd(C, full_matrices=False)
            if np.any(s) == 0.0:
                raise RuntimeError("Expansion points not linearly independent")
            inv = np.einsum("pji,pj,pkj,pk,pk->pi", vh, 1.0 / s, u, weight, yields)
            M = mat(inv, n=n)
            if algo == "svd_pos":
                eig, eigv = np.linalg.eigh(M)
                eigp = np.maximum(eig, tol)  # magic happens here
                M = (eigv * eigp[:, None, :]) @ np.swapaxes(eigv, 1, 2)
            self._M = M
        elif algo == "dcp":
            import cvxpy as cp

            Mall = np.empty((nbin, n, n))
            M = cp.Variable((n, n), PSD=True)
            for i in range(nbin):
                c = points * np.sqrt(weight[i, :, None])
                y = yields[i] * weight[i]
                obj = cp.Minimize(
                    sum((cp.quad_form(c[j], M) - y[j]) ** 2 for j in range(npt))
                )
                prob = cp.Problem(obj, [M >> tol])
                rss = prob.solve()
                if prob.status == cp.OPTIMAL:
                    pass
                elif prob.status == cp.OPTIMAL_INACCURATE:
                    warnings.warn(f"Inaccurate solution for bin {i} (rss={rss})")
                else:
                    raise RuntimeError(
                        f"Unable to solve problem for bin {i} (rss={rss}, status={prob.status})"
                    )
                Mall[i] = M.value
            self._M = Mall
        elif algo == "scs":
            import scipy.sparse
            import scs

            Mall = np.empty((nbin, n, n))
            k = n * (n + 1) // 2
            data = dict(
                A=-scipy.sparse.csc_matrix(np.eye(k)),
                b=np.zeros(k),
            )
            cone = dict(s=n)
            for i in range(nbin):
                cw = points * np.sqrt(weight[i, :, None])
                yw = yields[i] * weight[i]
                D = vec(cw[:, None, :] * cw[:, :, None])
                data["P"] = scipy.sparse.csc_matrix(D.T @ D)
                data["c"] = -yw @ D
                ywsq = max(yw @ yw, 1.0)
                sol = scs.solve(
                    data, cone, verbose=False, eps_abs=tol, eps_rel=min(tol, 1 / ywsq)
                )
                M = mat(sol["s"], n=n)
                if sol["info"]["status_val"] == 1:
                    pass
                else:
                    rss = sol["s"] @ D.T @ D @ sol["s"] - 2 * yw @ D @ sol["s"] + ywsq
                    raise RuntimeError(
                        f"Unable to solve problem for bin {i} (rss={rss}, status={sol['info']})"
                    )
                Mall[i] = M
            self._M = Mall

    def __call__(self, c):
        if self._M is None:
            raise RuntimeError("Please call solve() first")
        return c @ self._M @ c
