import warnings
import numpy as np
from collections import OrderedDict
import matplotlib.pyplot as plt
import mplhep as hep
plt.style.use(hep.style.ROOT)


def tril_ravel(M):
    i, j = np.tril_indices(M.shape[-1])
    return M[..., i, j] * (1 + i != j)


def tril_unravel(v):
    vl = v.shape[-1]
    n = int(0.5 * (np.sqrt(1 + 8 * vl) - 1))
    M = np.zeros(v.shape[:-1] + (n, n))
    i, j = np.tril_indices(n)
    M[..., i, j] += 0.5 * v
    M[..., j, i] += 0.5 * v
    return M


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
            C = tril_ravel(points[:, None, :] * points[:, :, None]) * weight[:, None]
            u, s, vh = np.linalg.svd(C, full_matrices=False)
            if np.any(s) == 0.0:
                raise RuntimeError("Expansion points not linearly independent")
            inv = np.einsum("pji,pj,pkj,pk,pk->pi", vh, 1.0 / s, u, weight, yields)
            M = tril_unravel(inv)
            if algo == "svd_pos":
                eig, eigv = np.linalg.eigh(M)
                eigp = np.maximum(eig, tol)  # magic happens here
                # M = (eigv * eigp[:, None, :]) @ np.swapaxes(eigv, 1, 2)
                M = np.matmul(eigv * eigp[:, None, :], np.swapaxes(eigv, 1, 2))
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
                    warnings.warn("Inaccurate solution for bin {i} (rss={rss})".format(i=i, rss=rss))
                else:
                    raise RuntimeError(
                        "Unable to solve problem for bin {i} (rss={rss}, status={status})".format(i=i, rss=rss, status=prob.status)
                    )
                Mall[i] = M.value
            self._M = Mall

    def __call__(self, c):
        if self._M is None:
            raise RuntimeError("Please call solve() first")
        # return c @ self._M @ c
        return np.matmul(np.matmul(c, self._M), c)


def qqHH_coef(CV=0.0, kl=0.0, C2V=0.0):
    return np.array([CV * kl, CV * CV, C2V])


def ggHH_coef(kl=0.0, kt=0.0):
    return np.array([kl * kt, kt * kt])


def get_abs_err(shape, logn_err):
    err = (logn_err - 1) * shape
    # set 0 bin error to something large?
    # err[err == 0] = shape.max()
    # instead set it to something smaller
    err[err == 0] = err[err.nonzero()].min()
    return err


def plot_shape(y, ynew, yerr, yerrnew, name):
    plt.figure()
    hep.histplot(y, range(0, len(y)+1), yerr=yerr, histtype='step', label='before')
    hep.histplot(ynew, range(0, len(ynew)+1), yerr=yerrnew, histtype='step', label='after', ls='--')
    plt.legend(title=name)
    plt.ylim(bottom=0)
    plt.savefig('{name}.png'.format(name=name))
    plt.close()


include_kl_0_kt_1 = True
if include_kl_0_kt_1:
    ggHH_points = OrderedDict([
        ("ggHH_kl_0_kt_1", ggHH_coef(kl=0, kt=1)),
        ("ggHH_kl_1_kt_1", ggHH_coef(kl=1, kt=1)),
        ("ggHH_kl_2p45_kt_1", ggHH_coef(kl=2.45, kt=1)),
        ("ggHH_kl_5_kt_1", ggHH_coef(kl=5, kt=1)),
    ])
else:
    ggHH_points = OrderedDict([
        ("ggHH_kl_1_kt_1", ggHH_coef(kl=1, kt=1)),
        ("ggHH_kl_2p45_kt_1", ggHH_coef(kl=2.45, kt=1)),
        ("ggHH_kl_5_kt_1", ggHH_coef(kl=5, kt=1)),
    ])

qqHH_points = OrderedDict([
    ("qqHH_CV_1_C2V_1_kl_1", qqHH_coef(CV=1, C2V=1, kl=1)),
    ("qqHH_CV_1_C2V_1_kl_0", qqHH_coef(CV=1, C2V=1, kl=0)),
    ("qqHH_CV_1_C2V_1_kl_2", qqHH_coef(CV=1, C2V=1, kl=2)),
    ("qqHH_CV_1_C2V_0_kl_1", qqHH_coef(CV=1, C2V=0, kl=1)),
    ("qqHH_CV_1_C2V_2_kl_1", qqHH_coef(CV=1, C2V=2, kl=1)),
    ("qqHH_CV_0p5_C2V_1_kl_1", qqHH_coef(CV=0.5, C2V=1, kl=1)),
    ("qqHH_CV_1p5_C2V_1_kl_1", qqHH_coef(CV=1.5, C2V=1, kl=1)),
])

if __name__ == "__main__":
    shapes = np.load("shapes.npz")
    errors = np.load("errors.npz")
    channel = "_hbbhbb"

    ggHH_zero_bins = []
    for name, c in ggHH_points.items():
        ggHH_zero_bins.append(shapes[name+channel] == 0)
    ggHH_zero_bins = np.stack(ggHH_zero_bins, axis=0)
    ggHH_zero_bins = np.all(ggHH_zero_bins, axis=0)
    ggHH_zero_bins = ggHH_zero_bins.nonzero()[0]

    qqHHproc = BasisPointExpansion(3)
    for name, c in qqHH_points.items():
        shape = shapes[name + channel]
        logn_err = errors[name + channel]
        err = get_abs_err(shape, logn_err)
        qqHHproc.add_point(c, shape, err)

    qqHHproc.solve("dcp")

    newpts = {}
    newerrs = {}
    for name, c in qqHH_points.items():
        ynew = qqHHproc(c)
        shape = shapes[name + channel]
        logn_err = errors[name + channel]
        err = get_abs_err(shape, logn_err)
        adiff = abs(ynew - shape)
        chi = adiff / err
        chi2 = np.sum(chi * chi)
        print("{name} lowest val {ymin} max diff {diff} chi2 {chi2}".format(
            name=name,
            ymin=ynew.min(),
            diff=adiff.max(),
            chi2=chi2)
        )
        print("old norm: {norm} +/- {err}".format(norm=np.sum(shape), err=np.sqrt(np.sum(np.square(err)))))
        print("new norm: {norm} +/- {err}".format(norm=np.sum(ynew), err=np.sqrt(np.sum(np.square(err)))))
        newpts[name + channel] = ynew
        newerrs[name + channel] = 1 + err/ynew
        plot_shape(shape, newpts[name + channel], (logn_err-1)*shape, (newerrs[name + channel]-1)*newpts[name + channel], name)

    ggHHproc = BasisPointExpansion(2)
    for name, c in ggHH_points.items():
        shape = shapes[name + channel]
        logn_err = errors[name + channel]
        err = get_abs_err(shape, logn_err)
        ggHHproc.add_point(c, shape, err)

    ggHHproc.solve("dcp")

    for name, c in ggHH_points.items():
        ynew = ggHHproc(c)
        shape = shapes[name + channel]
        logn_err = errors[name + channel]
        err = get_abs_err(shape, logn_err)
        adiff = abs(ynew - shape)
        reldiff = adiff/shape
        chi = adiff / err
        chi2 = np.sum(chi * chi)
        print("{name} lowest val {ymin} max diff {diff} chi2 {chi2}".format(
            name=name,
            ymin=ynew.min(),
            diff=adiff.max(),
            chi2=chi2)
        )
        print("old norm: {norm} +/- {err}".format(norm=np.sum(shape), err=np.sqrt(np.sum(np.square(err)))))
        print("new norm: {norm} +/- {err}".format(norm=np.sum(ynew), err=np.sqrt(np.sum(np.square(err)))))
        newpts[name + channel] = ynew
        newerrs[name + channel] = 1 + err/ynew
        newpts[name + channel][ggHH_zero_bins] = 0
        newerrs[name + channel][ggHH_zero_bins] = 1
        plot_shape(shape, newpts[name + channel], (logn_err - 1)*shape, (newerrs[name + channel] - 1)*newpts[name + channel], name)

    if include_kl_0_kt_1:
        np.savez("newshapes.npz", **newpts)
        np.savez("newerrors.npz", **newerrs)
    else:
        np.savez("newshapes_no_kl_0_kt_1.npz", **newpts)
        np.savez("newerrors_no_kl_0_kt_1.npz", **newerrs)
