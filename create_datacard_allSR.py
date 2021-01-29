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

    msdbins = np.linspace(50, nbins*10.0+50.0, nbins+1)
    msd = rl.Observable('msd', msdbins)
    msdpts = msdbins[:-1] + 0.5 * np.diff(msdbins)
    msdscaled = (msdpts - 50.)/(10.0*nbins)

    # Build qcd MC pass+fail model and fit to polynomial
    qcdmodel = rl.Model('qcdmodel')
    failCh = rl.Channel('fail')
    passCh = rl.Channel('pass')
    srfailCh = rl.Channel('SRfail')
    srpassCh = rl.Channel('SR')
    qcdmodel.addChannel(failCh)
    qcdmodel.addChannel(passCh)
    qcdmodel.addChannel(srpassCh)

    # pseudodata MC template
    failTempl = get_hist(inputfile, 'histJet2MassBlind_'+failBinName+'_QCD', obs=msd)
    passTempl = get_hist(inputfile, 'histJet2MassBlind_'+passBinName+'_QCD', obs=msd)
    srfailTempl = get_hist(inputfile, 'histJet2MassSR_'+failBinName+'_QCD', obs=msd)
    srpassTempl = get_hist(inputfile, 'histJet2MassSR_'+passBinName+'_QCD', obs=msd)

    failCh.setObservation(failTempl[:-1])
    passCh.setObservation(passTempl[:-1])

    srfailCh.setObservation(srfailTempl[:-1])
    srpassCh.setObservation(srpassTempl[:-1])

    qcdpass = passCh.getObservation().sum()

    qcdsrfail = srfailCh.getObservation().sum()

    qcdeffpass = qcdpass / qcdsrfail
    qcdeffsr = qcdpass / qcdsrfail

    # transfer factor
    tf_dataResidual = rl.BernsteinPoly("tf_dataResidual_"+passBinName, (nDataTF,), ['msd'], limits=(0, 10))
    tf_dataResidual_params = tf_dataResidual(msdscaled)
    tf_params_pass = qcdeffpass * tf_dataResidual_params
    tf_params_sr = qcdeffsr * tf_dataResidual_params

    # build actual fit model now
    model = rl.Model("HHModel")
    for region in ['pass'+passBinName, 'fail', 'SR'+passBinName, 'SRfail']:
        ch = rl.Channel(region)
        model.addChannel(ch)

        isPass = region == 'pass'+passBinName
        isSR = region == 'SR'+passBinName
        isSRfail = region == 'SRfail'

        catn = 'Blind_'+passBinName
        if not isPass:
            if isSR:
                catn = 'SR_'+passBinName
            elif isSRfail:
                catn = 'SR_fail'
            else:
                catn = 'Blind_'+failBinName

        templates = {
            'TTJets': get_hist(inputfile, 'histJet2Mass'+catn+'_TTJets', obs=msd),
            'H': get_hist(inputfile, 'histJet2Mass'+catn+'_H', obs=msd),
            'HH': get_hist(inputfile, 'histJet2Mass'+catn+'_HH', obs=msd),
            'VH': get_hist(inputfile, 'histJet2Mass'+catn+'_VH', obs=msd),
            'ttH': get_hist(inputfile, 'histJet2Mass'+catn+'_ttH', obs=msd),
            'others': get_hist(inputfile, 'histJet2Mass'+catn+'_others', obs=msd),
            'QCD': get_hist(inputfile, 'histJet2Mass'+catn+'_QCD', obs=msd),
            'Data': get_hist(inputfile, 'histJet2Mass'+catn+'_Data', obs=msd),
        }
        for sName in ['TTJets', 'H', 'HH', 'VH', 'ttH', 'others']:
            # get templates
            templ = templates[sName]
            stype = rl.Sample.SIGNAL if sName == 'HH' else rl.Sample.BACKGROUND
            sample = rl.TemplateSample(ch.name + '_' + sName, stype, templ)

            # set nuisance values
            sample.setParamEffect(lumi, 1.027)

            # shape systematics
            valuesNominal = templ[0]
            systs = ['JMS', 'JMR', 'BDTMassShape', 'ttJetsCorr', 'BDTShape', 'PNetShape']
            for syst in systs:
                valuesUp = get_hist(inputfile, 'histJet2Mass'+catn+'_%s_%sUp' % (sName, syst), obs=msd)[0]
                valuesDown = get_hist(inputfile, 'histJet2Mass'+catn+'_%s_%sDown' % (sName, syst), obs=msd)[0]
                effectUp = np.ones_like(valuesNominal)
                effectDown = np.ones_like(valuesNominal)
                for i in range(len(valuesNominal)):
                    if valuesNominal[i] > 0.:
                        effectUp[i] = valuesUp[i]/valuesNominal[i]
                        effectDown[i] = valuesDown[i]/valuesNominal[i]

                syst_param = rl.NuisanceParameter(syst, 'shape')
                sample.setParamEffect(syst_param, effectUp, effectDown)

            ch.addSample(sample)

        # make up a data_obs by summing the MC templates above
        yields = templates['Data'][0]
        data_obs = (yields, msd.binning, msd.name)
        ch.setObservation(data_obs)

    failCh = model['fail']
    passCh = model['pass'+passBinName]

    srfailCh = model['SRfail']
    srCh = model['SR'+passBinName]

    qcdparams = np.array([rl.IndependentParameter('qcdparam_msdbin%d' % i, 0) for i in range(msd.nbins)])

    # sideband fail
    initial_qcd = failCh.getObservation().astype(float)  # was integer, and numpy complained about subtracting float from it
    for sample in failCh:
        initial_qcd -= sample.getExpectation(nominal=True)
    if np.any(initial_qcd < 0.):
        raise ValueError("initial_qcd negative for some bins..", initial_qcd)
    sigmascale = 10  # to scale the deviation from initial
    scaledparams = initial_qcd * (1 + sigmascale/np.maximum(1., np.sqrt(initial_qcd)))**qcdparams

    # signal region fail
    initial_qcd_sr = srfailCh.getObservation().astype(float)  # was integer, and numpy complained about subtracting float from it
    for sample in srfailCh:
        initial_qcd_sr -= sample.getExpectation(nominal=True)
    if np.any(initial_qcd_sr < 0.):
        raise ValueError("initial_qcd_sr negative for some bins..", initial_qcd_sr)
    scaledparams_sr = initial_qcd_sr * (1 + sigmascale/np.maximum(1., np.sqrt(initial_qcd_sr)))**qcdparams

    fail_qcd = rl.ParametericSample('fail_qcd', rl.Sample.BACKGROUND, msd, scaledparams)
    failCh.addSample(fail_qcd)

    # name: channel name _ proc name
    fail_qcd_sr = rl.ParametericSample('SRfail_qcd', rl.Sample.BACKGROUND, msd, scaledparams_sr)
    srfailCh.addSample(fail_qcd_sr)

    pass_qcd = rl.TransferFactorSample('pass'+passBinName+'_qcd', rl.Sample.BACKGROUND, tf_params_pass, fail_qcd)
    passCh.addSample(pass_qcd)

    sr_qcd = rl.TransferFactorSample('SR'+passBinName+'_qcd', rl.Sample.BACKGROUND, tf_params_sr, fail_qcd_sr)
    srCh.addSample(sr_qcd)

    with open(os.path.join(str(carddir), 'HHModel.pkl'), "wb") as fout:
        pickle.dump(model, fout)

    model.renderCombine(os.path.join(str(carddir), 'HHModel'))


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--inputfile', default='HHTo4BPlots_Run2_BDTv24.root', type=str, dest='inputfile', help='input ROOT file')
    parser.add_argument('--carddir', default='cards', type=str, dest='carddir', help='output card directory')
    parser.add_argument('--nbins', default=17, type=int, dest='nbins', help='number of bins')
    parser.add_argument('--nMCTF', default=0, type=int, dest='nMCTF', help='order of polynomial for TF from MC')
    parser.add_argument('--nDataTF', default=2, type=int, dest='nDataTF', help='order of polynomial for TF from Data')

    args = parser.parse_args()
    import pathlib2 as pathlib
    pathlib.Path(args.carddir).mkdir(parents=True, exist_ok=True) 

    for fitbin in ["Bin1", "Bin2", "Bin3", "Bin4"]:
        fitdir = os.path.join(args.carddir, 'cards_{}'.format(fitbin))
        pathlib.Path(fitdir).mkdir(parents=True, exist_ok=True)
        create_datacard(args.inputfile, fitdir, args.nbins, args.nMCTF, args.nDataTF, fitbin, "fail")
