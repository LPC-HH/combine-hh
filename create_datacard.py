from __future__ import print_function, division
import os
import rhalphalib as rl
import numpy as np
import pickle
import uproot
rl.util.install_roofit_helpers()
rl.ParametericSample.PreferRooParametricHist = False


def get_hist(inputfile, name, obs):
    upfile = uproot.open(inputfile)
    hist_values = upfile[name].values()
    hist_edges = upfile[name].axis().edges()
    hist_uncs = upfile[name].variances()
    if obs.binning != hist_edges:
        # rebin (assumes new bins are a subset of existing bins)
        edge_mask = np.in1d(hist_edges, obs.binning)
        hist_mask = np.logical_and(edge_mask[0:-1], edge_mask[1:])
        hist_values = hist_values[hist_mask]
        hist_edges = hist_edges[edge_mask]
        hist_uncs = hist_uncs[hist_mask]
    return (hist_values, hist_edges, obs.name, hist_uncs)


def create_datacard(inputfile, carddir, nbins, nMCTF, nDataTF, passBinName, failBinName):
    lumi = rl.NuisanceParameter('CMS_lumi', 'lnN')
    trigSF = rl.NuisanceParameter('triggerEffSFSyst', 'lnN')
    PNetHbbScaleFactorssyst = rl.NuisanceParameter('PNetHbbScaleFactors_correlated', 'lnN')

    msdbins = np.linspace(50, nbins*10.0+50.0, nbins+1)
    msd = rl.Observable('msd', msdbins)
    msdpts = msdbins[:-1] + 0.5 * np.diff(msdbins)
    msdscaled = (msdpts - 50.)/(10.0*nbins)

    # Build qcd MC pass+fail model and fit to polynomial
    qcdmodel = rl.Model('qcdmodel')
    qcdpass, qcdfail = 0., 0.
    failCh = rl.Channel('fail')
    passCh = rl.Channel('pass')
    qcdmodel.addChannel(failCh)
    qcdmodel.addChannel(passCh)

    # pseudodata MC template
    failTempl = get_hist(inputfile, 'histJet2MassBlind_fail_QCD', obs=msd)
    passTempl = get_hist(inputfile, 'histJet2MassBlind_'+passBinName+'_QCD', obs=msd)

    failCh.setObservation(failTempl[:-1])
    passCh.setObservation(passTempl[:-1])
    qcdfail = failCh.getObservation().sum()
    qcdpass = passCh.getObservation().sum()

    qcdeff = qcdpass / qcdfail

    # transfer factor
    tf_dataResidual = rl.BernsteinPoly("tf_dataResidual", (nDataTF,), ['msd'], limits=(-10, 10))
    tf_dataResidual_params = tf_dataResidual(msdscaled)
    tf_params = qcdeff * tf_dataResidual_params

    # build actual fit model now
    model = rl.Model("HHModel")
    for region in ['pass', 'fail']:
        ch = rl.Channel(region)
        model.addChannel(ch)

        isPass = region == 'pass'

        if isPass:
            catn = 'Blind_'+passBinName
        else:
            catn = 'Blind_'+failBinName

        templates = {
            'TTJets': get_hist(inputfile, 'histJet2Mass'+catn+'_TTJets', obs=msd),
            'ggHH_kl_1_kt_1_boost4b': get_hist(inputfile, 'histJet2Mass'+catn+'_ggHH_kl_1_kt_1_boost4b', obs=msd),
            'qqHH_CV_1_C2V_1_kl_1_boost4b': get_hist(inputfile, 'histJet2Mass'+catn+'_qqHH_CV_1_C2V_1_kl_1_boost4b', obs=msd),
            'VH': get_hist(inputfile, 'histJet2Mass'+catn+'_VH', obs=msd),
            'ttH': get_hist(inputfile, 'histJet2Mass'+catn+'_ttH', obs=msd),
            'others': get_hist(inputfile, 'histJet2Mass'+catn+'_others', obs=msd),
            'QCD': get_hist(inputfile, 'histJet2Mass'+catn+'_QCD', obs=msd),
            'Data': get_hist(inputfile, 'histJet2Mass'+catn+'_Data', obs=msd),
        }

        systs = [
            'ttbarBin1Jet2PNetCut',
            'FSRPartonShower',
            'ISRPartonShower',
            'ggHHPDFacc',
            'ggHHQCDacc',
            'pileupWeight',
            'JER',
            'JES',
            'JMS',
            'JMR',
            'ttJetsCorr',
            'BDTShape',
            'PNetShape',
            'PNetHbbScaleFactors',
            'triggerEffSF']

        syst_param_array = []
        for i in range(len(systs)):
            syst_param_array.append(rl.NuisanceParameter(systs[i], 'shape'))

        for sName in ['TTJets', 'ggHH_kl_1_kt_1_boost4b', 'qqHH_CV_1_C2V_1_kl_1_boost4b', 'VH', 'ttH', 'others']:
            # get templates
            templ = templates[sName]
            stype = rl.Sample.SIGNAL if 'HH' in sName else rl.Sample.BACKGROUND
            sample = rl.TemplateSample(ch.name + '_' + sName, stype, templ)

            # set nuisance values
            sample.setParamEffect(lumi, 1.016)
            sample.setParamEffect(trigSF, 1.04)

            if ("VH" in sName) or ("ttH" in sName):
                print("sName and PNetSF 5%: ", sName)
                sample.setParamEffect(PNetHbbScaleFactorssyst, 1.04)
            elif "HH" in sName:
                print("sName and PNetSF 10%: ", sName)
                sample.setParamEffect(PNetHbbScaleFactorssyst, 1.0816)

            # set mc stat uncs
            sample.autoMCStats()

            # shape systematics
            valuesNominal = templ[0]

            isyst = 0
            for syst in systs:
                valuesUp = get_hist(inputfile, 'histJet2Mass'+catn+'_%s_%sUp' % (sName, syst), obs=msd)[0]
                valuesDown = get_hist(inputfile, 'histJet2Mass'+catn+'_%s_%sDown' % (sName, syst), obs=msd)[0]
                effectUp = np.ones_like(valuesNominal)
                effectDown = np.ones_like(valuesNominal)
                for i in range(len(valuesNominal)):
                    if valuesNominal[i] > 0.:
                        effectUp[i] = valuesUp[i]/valuesNominal[i]
                        effectDown[i] = valuesDown[i]/valuesNominal[i]
                sample.setParamEffect(syst_param_array[isyst], effectUp, effectDown)
                isyst = isyst + 1
            ch.addSample(sample)

        # data observed
        yields = templates['Data'][0]
        data_obs = (yields, msd.binning, msd.name)
        ch.setObservation(data_obs)

    failCh = model['fail']
    passCh = model['pass']

    qcdparams = np.array([rl.IndependentParameter('qcdparam_msdbin%d' % i, 0) for i in range(msd.nbins)])

    # fail
    initial_qcd = failCh.getObservation().astype(float)  # was integer, and numpy complained about subtracting float from it
    for sample in failCh:
        initial_qcd -= sample.getExpectation(nominal=True)
    if np.any(initial_qcd < 0.):
        raise ValueError("initial_qcd negative for some bins..", initial_qcd)
    sigmascale = 10  # to scale the deviation from initial
    scaledparams = initial_qcd * (1 + sigmascale/np.maximum(1., np.sqrt(initial_qcd)))**qcdparams

    # add samples
    fail_qcd = rl.ParametericSample('fail_qcd', rl.Sample.BACKGROUND, msd, scaledparams)
    failCh.addSample(fail_qcd)

    pass_qcd = rl.TransferFactorSample('pass_qcd', rl.Sample.BACKGROUND, tf_params, fail_qcd)
    passCh.addSample(pass_qcd)

    with open(os.path.join(str(carddir), 'HHModel.pkl'), "wb") as fout:
        pickle.dump(model, fout)

    model.renderCombine(os.path.join(str(carddir), 'HHModel'))


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--inputfile', default='HHTo4BPlots_Run2_BDTv8p2.root', type=str, dest='inputfile', help='input ROOT file')
    parser.add_argument('--carddir', default='cards', type=str, dest='carddir', help='output card directory')
    parser.add_argument('--nbins', default=17, type=int, dest='nbins', help='number of bins')
    parser.add_argument('--nMCTF', default=0, type=int, dest='nMCTF', help='order of polynomial for TF from MC')
    parser.add_argument('--nDataTF', default=2, type=int, dest='nDataTF', help='order of polynomial for TF from Data')
    parser.add_argument('--passBinName', default='Bin1', type=str, choices=['Bin1', 'Bin2', 'Bin3'], help='pass bin name')

    args = parser.parse_args()
    if not os.path.exists(args.carddir):
        os.mkdir(args.carddir)
    create_datacard(args.inputfile, args.carddir, args.nbins, args.nMCTF, args.nDataTF, args.passBinName, "fail")
