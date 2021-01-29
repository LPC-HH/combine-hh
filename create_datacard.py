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
    qcdpass, qcdfail = 0., 0.
    failCh = rl.Channel('fail')
    passCh = rl.Channel('pass')
    qcdmodel.addChannel(failCh)
    qcdmodel.addChannel(passCh)
    # pseudodata MC template
    failTempl = get_hist(inputfile, 'histJet2MassBlind_'+failBinName+'_QCD', obs=msd)
    passTempl = get_hist(inputfile, 'histJet2MassBlind_'+passBinName+'_QCD', obs=msd)
    failCh.setObservation(failTempl[:-1])
    passCh.setObservation(passTempl[:-1])
    qcdfail = failCh.getObservation().sum()
    qcdpass = passCh.getObservation().sum()

    qcdeff = qcdpass / qcdfail
    tf_dataResidual = rl.BernsteinPoly("tf_dataResidual", (nDataTF,), ['msd'], limits=(0, 10))
    tf_dataResidual_params = tf_dataResidual(msdscaled)
    tf_params = qcdeff * tf_dataResidual_params

    # build actual fit model now
    model = rl.Model("HHModel")
    for region in ['pass', 'fail']:
        ch = rl.Channel(region)
        model.addChannel(ch)

        isPass = region == 'pass'
        templates = {
            'TTJets': get_hist(inputfile, 'histJet2MassBlind%s_TTJets' % ('_'+passBinName if isPass else '_'+failBinName), obs=msd),
            'H': get_hist(inputfile, 'histJet2MassBlind%s_H' % ('_'+passBinName if isPass else '_'+failBinName), obs=msd),
            'HH': get_hist(inputfile, 'histJet2MassBlind%s_HH' % ('_'+passBinName if isPass else '_'+failBinName), obs=msd),
            'VH': get_hist(inputfile, 'histJet2MassBlind%s_VH' % ('_'+passBinName if isPass else '_'+failBinName), obs=msd),
            'ttH': get_hist(inputfile, 'histJet2MassBlind%s_ttH' % ('_'+passBinName if isPass else '_'+failBinName), obs=msd),
            'others': get_hist(inputfile, 'histJet2MassBlind%s_others' % ('_'+passBinName if isPass else '_'+failBinName), obs=msd),
            'QCD': get_hist(inputfile, 'histJet2MassBlind%s_QCD' % ('_'+passBinName if isPass else '_'+failBinName), obs=msd),
            'Data': get_hist(inputfile, 'histJet2MassBlind%s_Data' % ('_'+passBinName if isPass else '_'+failBinName), obs=msd),
        }
        for sName in ['TTJets', 'H', 'HH', 'VH', 'ttH', 'others']:
            # get templates
            templ = templates[sName]
            stype = rl.Sample.SIGNAL if sName == 'HH' else rl.Sample.BACKGROUND
            sample = rl.TemplateSample(ch.name + '_' + sName, stype, templ)

            # set nuisance values
            sample.setParamEffect(lumi, 1.027)

            # set mc stat uncs
            sample.autoMCStats()

            # shape systematics
            valuesNominal = templ[0]
            systs = ['JMS', 'JMR', 'BDTMassShape', 'ttJetsCorr', 'BDTShape', 'PNetShape']
            for syst in systs:
                valuesUp = get_hist(inputfile, 'histJet2MassBlind%s_%s_%sUp' % ('_'+passBinName if isPass else '_'+failBinName, sName, syst), obs=msd)[0]
                valuesDown = get_hist(inputfile, 'histJet2MassBlind%s_%s_%sDown' % ('_'+passBinName if isPass else '_'+failBinName, sName, syst), obs=msd)[0]
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
    passCh = model['pass']

    qcdparams = np.array([rl.IndependentParameter('qcdparam_msdbin%d' % i, 0) for i in range(msd.nbins)])
    initial_qcd = failCh.getObservation().astype(float)  # was integer, and numpy complained about subtracting float from it
    for sample in failCh:
        initial_qcd -= sample.getExpectation(nominal=True)
    if np.any(initial_qcd < 0.):
        raise ValueError("initial_qcd negative for some bins..", initial_qcd)
    sigmascale = 10  # to scale the deviation from initial
    scaledparams = initial_qcd * (1 + sigmascale/np.maximum(1., np.sqrt(initial_qcd)))**qcdparams
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
    parser.add_argument('--inputfile', default='HHTo4BPlots_Run2_BDTv24.root', type=str, dest='inputfile', help='input ROOT file')
    parser.add_argument('--carddir', default='cards', type=str, dest='carddir', help='output card directory')
    parser.add_argument('--nbins', default=17, type=int, dest='nbins', help='number of bins')
    parser.add_argument('--nMCTF', default=0, type=int, dest='nMCTF', help='order of polynomial for TF from MC')
    parser.add_argument('--nDataTF', default=2, type=int, dest='nDataTF', help='order of polynomial for TF from Data')

    args = parser.parse_args()
    import pathlib2 as pathlib
    pathlib.Path(args.carddir).mkdir(parents=True, exist_ok=True)

    create_datacard(args.inputfile, args.carddir, args.nbins, args.nMCTF, args.nDataTF, "Bin4", "fail")
