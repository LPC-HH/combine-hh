from __future__ import print_function, division
import os
import rhalphalib as rl
import numpy as np
import pickle
from create_datacard import get_hist
rl.util.install_roofit_helpers()
rl.ParametericSample.PreferRooParametricHist = False


def create_datacard(inputfile, carddir, nbins, nMCTF, nDataTF, passBinName, failBinName):
    ttbarBin1MCstats = rl.NuisanceParameter('ttbarBin1_yieldMCStats', 'lnN')
    lumi = rl.NuisanceParameter('CMS_lumi', 'lnN')
    trigSF = rl.NuisanceParameter('triggerEffSF_correlated', 'lnN')
    PNetHbbScaleFactorssyst = rl.NuisanceParameter('PNetHbbScaleFactors_correlated', 'lnN')

    msdbins = np.linspace(50, nbins*10.0+50.0, nbins+1)
    msd = rl.Observable('msd', msdbins)
    msdpts = msdbins[:-1] + 0.5 * np.diff(msdbins)
    msdscaled = (msdpts - 50.)/(10.0*nbins)

    # Build qcd MC pass+fail model and fit to polynomial
    qcdmodel = rl.Model('qcdmodel')
    qcdpass, qcdfitfail = 0., 0.
    passCh = rl.Channel('passqcdmodel')
    fitfailCh = rl.Channel('fitfailqcdmodel')
    qcdmodel.addChannel(fitfailCh)
    qcdmodel.addChannel(passCh)

    # pseudodata MC template
    passTempl = get_hist(inputfile, 'histJet2MassBlind_'+passBinName+'_QCD', obs=msd)
    fitfailTempl = get_hist(inputfile, 'histJet2Massfit_fail_QCD', obs=msd)

    passCh.setObservation(passTempl[:-1])
    fitfailCh.setObservation(fitfailTempl[:-1])
    qcdpass = passCh.getObservation().sum()
    qcdfitfail = fitfailCh.getObservation().sum()

    qcdeffpass = qcdpass / qcdfitfail

    # transfer factor
    tf_dataResidual = rl.BernsteinPoly("tf_dataResidual_"+passBinName, (nDataTF,), ['msd'], limits=(-20, 20))
    tf_dataResidual_params = tf_dataResidual(msdscaled)
    tf_params_pass = qcdeffpass * tf_dataResidual_params

    # build actual fit model now
    model = rl.Model("HHModel")
    for region in ['pass'+passBinName, 'fail', 'SR'+passBinName, 'fitfail']:
        ch = rl.Channel(region)
        model.addChannel(ch)

        isPass = region == 'pass'+passBinName
        isSR = region == 'SR'+passBinName
        isfitfail = region == 'fitfail'

        if isPass:
            catn = 'Blind_'+passBinName
        elif isSR:
            catn = '_'+passBinName
        elif isfitfail:
            catn = 'fit_'+failBinName
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

        systs_name_in_cards = ['ttbarBin1Jet2PNetCut', 'FSRPartonShower', 'ISRPartonShower', 'ggHHPDFacc', 'ggHHQCDacc',
                               'CMS_pileup', 'CMS_JER', 'CMS_JES', 'CMS_JMS', 'CMS_JMR', 'ttJetsCorr', 'ttJetsBDTShape',
                               'ttJetsPNetShape', 'PNetHbbScaleFactors_uncorrelated', 'triggerEffSF_uncorrelated']

        syst_param_array = []
        for i in range(len(systs)):
            syst_param_array.append(rl.NuisanceParameter(systs_name_in_cards[i], 'shape'))

        for sName in ['TTJets', 'ggHH_kl_1_kt_1_boost4b', 'qqHH_CV_1_C2V_1_kl_1_boost4b', 'VH', 'ttH', 'others']:
            # get templates
            templ = templates[sName]
            stype = rl.Sample.SIGNAL if 'HH' in sName else rl.Sample.BACKGROUND
            sample = rl.TemplateSample(ch.name + '_' + sName, stype, templ)

            sample.setParamEffect(lumi, 1.016)
            sample.setParamEffect(trigSF, 1.04)

            if ("TTJets" == sName and "Bin1" in region):
                if ("passBin1" == region):
                    sample.setParamEffect(ttbarBin1MCstats, 1.215)
                elif ("SRBin1" == region):
                    sample.setParamEffect(ttbarBin1MCstats, 1.187)

            if ("VH" in sName) or ("ttH" in sName):
                sample.setParamEffect(PNetHbbScaleFactorssyst, 1.04)
            elif "HH" in sName:
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
    passCh = model['pass'+passBinName]
    srCh = model['SR'+passBinName]
    fitfailCh = model['fitfail']

    qcdparams = np.array([rl.IndependentParameter('qcdparam_msdbin%d' % i, 0) for i in range(msd.nbins)])

    # sideband fail
    initial_qcd = failCh.getObservation().astype(float)  # was integer, and numpy complained about subtracting float from it
    for sample in failCh:
        initial_qcd -= sample.getExpectation(nominal=True)
    if np.any(initial_qcd < 0.):
        raise ValueError("initial_qcd negative for some bins..", initial_qcd)
    sigmascale = 10  # to scale the deviation from initial
    scaledparams = initial_qcd * (1 + sigmascale/np.maximum(1., np.sqrt(initial_qcd)))**qcdparams

    # fit region fail
    initial_qcd_fit = fitfailCh.getObservation().astype(float)  # was integer, and numpy complained about subtracting float from it
    for sample in fitfailCh:
        initial_qcd_fit -= sample.getExpectation(nominal=True)
    if np.any(initial_qcd_fit < 0.):
        raise ValueError("initial_qcd_fit negative for some bins..", initial_qcd_fit)
    scaledparams_fit = initial_qcd_fit * (1 + sigmascale/np.maximum(1., np.sqrt(initial_qcd_fit)))**qcdparams

    # add samples
    fail_qcd = rl.ParametericSample('fail_qcd', rl.Sample.BACKGROUND, msd, scaledparams)
    failCh.addSample(fail_qcd)

    fail_qcd_fit = rl.ParametericSample('fitfail_qcd', rl.Sample.BACKGROUND, msd, scaledparams_fit)
    fitfailCh.addSample(fail_qcd_fit)

    pass_qcd = rl.TransferFactorSample('pass'+passBinName+'_qcd', rl.Sample.BACKGROUND, tf_params_pass, fail_qcd)
    passCh.addSample(pass_qcd)

    sr_qcd = rl.TransferFactorSample('SR'+passBinName+'_qcd', rl.Sample.BACKGROUND, tf_params_pass, fail_qcd_fit)
    srCh.addSample(sr_qcd)

    with open(os.path.join(str(carddir), 'HHModel.pkl'), "wb") as fout:
        pickle.dump(model, fout)

    model.renderCombine(os.path.join(str(carddir), 'HHModel'))


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--inputfile', default='HHTo4BPlots_Run2_BDTv8p2_0311_syst_Trigv0.root', type=str, dest='inputfile', help='input ROOT file')
    parser.add_argument('--carddir', default='cards', type=str, dest='carddir', help='output card directory')
    parser.add_argument('--nbins', default=17, type=int, dest='nbins', help='number of bins')

    args = parser.parse_args()
    if not os.path.exists("cards"):
        os.mkdir("cards")
    if not os.path.exists("cards/"+args.carddir):
        os.mkdir("cards/"+args.carddir)

    binNames = ['Bin1', 'Bin2', 'Bin3']

    nDataTFDict = {}  # order of data TF polynomial
    nDataTFDict['Bin1'] = 0
    nDataTFDict['Bin2'] = 1
    nDataTFDict['Bin3'] = 0

    for fitbin in binNames:
        os.system("rm -rf cards/"+args.carddir+"/cards_"+fitbin)
        os.system("mkdir cards/"+args.carddir+"/cards_"+fitbin)

        create_datacard(args.inputfile, "cards/"+args.carddir+"/cards_"+fitbin, args.nbins, 0, nDataTFDict[fitbin], fitbin, "fail")
