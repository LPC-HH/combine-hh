import warnings
import numpy as np
from collections import OrderedDict
from bpe import BasisPointExpansion
import matplotlib.pyplot as plt
import mplhep as hep
plt.style.use(hep.style.ROOT)


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


    ggHHproc = BasisPointExpansion(2)
    for name, c in ggHH_points.items():
        shape = shapes[name + channel]
        logn_err = errors[name + channel]
        err = get_abs_err(shape, logn_err)
        ggHHproc.add_point(c, shape, err)

    qqHHproc.solve("dcp", tol=1e-9)
    ggHHproc.solve("dcp", tol=1e-9)

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
        newerrs[name + channel][ynew==0] = 1
        plot_shape(shape, newpts[name + channel], (logn_err-1)*shape, (newerrs[name + channel]-1)*newpts[name + channel], name)

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
        newerrs[name + channel][ynew==0] = 1
        newpts[name + channel][ggHH_zero_bins] = 0
        newerrs[name + channel][ggHH_zero_bins] = 1
        plot_shape(shape, newpts[name + channel], (logn_err - 1)*shape, (newerrs[name + channel] - 1)*newpts[name + channel], name)

    if include_kl_0_kt_1:
        np.savez("newshapes.npz", **newpts)
        np.savez("newerrors.npz", **newerrs)
    else:
        np.savez("newshapes_no_kl_0_kt_1.npz", **newpts)
        np.savez("newerrors_no_kl_0_kt_1.npz", **newerrs)
