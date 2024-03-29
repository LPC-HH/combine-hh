from __future__ import print_function, division
import os
import rhalphalib as rl
import numpy as np
import pickle
import uproot
import logging
import sys
from collections import OrderedDict
rl.util.install_roofit_helpers()
rl.ParametericSample.PreferRooParametricHist = False
logging.basicConfig(level=logging.DEBUG)
adjust_posdef_yields = False


def get_hist(upfile, name, obs):
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


def symmetrize(effectUp, effectDown):
    envelopeUp = np.maximum(effectUp, effectDown)
    envelopeDown = np.minimum(effectUp, effectDown)
    effectUpSym = np.sqrt(envelopeUp/envelopeDown)
    effectDownSym = np.sqrt(envelopeDown/envelopeUp)
    return effectUpSym, effectDownSym


def create_datacard(inputfile, carddir, nbins, nMCTF, nDataTF, passBinName, failBinName='fail', add_blinded=False, include_ac=False):

    # open uproot file once
    upfile = uproot.open(inputfile)

    regionPairs = [('SR'+passBinName, 'fit'+failBinName)]  # pass, fail region pairs
    if add_blinded:
        regionPairs += [('pass'+passBinName, failBinName)]  # add sideband region pairs

    regions = [item for t in regionPairs for item in t]  # all regions

    # luminosity unc https://gitlab.cern.ch/hh/naming-conventions#luminosity
    lumi_16 = 36.33
    lumi_17 = 41.48
    lumi_18 = 59.83
    lumi_run2 = lumi_16 + lumi_17 + lumi_18
    lumi_13TeV_2016 = rl.NuisanceParameter('lumi_13TeV_2016', 'lnN')
    lumi_13TeV_2017 = rl.NuisanceParameter('lumi_13TeV_2017', 'lnN')
    lumi_13TeV_2018 = rl.NuisanceParameter('lumi_13TeV_2018', 'lnN')
    lumi_13TeV_correlated = rl.NuisanceParameter('lumi_13TeV_correlated', 'lnN')
    lumi_13TeV_1718 = rl.NuisanceParameter('lumi_13TeV_1718', 'lnN')
    ttbarBin1MCstats = rl.NuisanceParameter('CMS_bbbb_boosted_ggf_ttbarBin1_yieldMCStats', 'lnN')
    PNetHbbScaleFactorssyst = rl.NuisanceParameter('CMS_bbbb_boosted_ggf_PNetHbbScaleFactors_correlated', 'lnN')
    brHbb = rl.NuisanceParameter('BR_hbb', 'lnN')
    pdfqqbar = rl.NuisanceParameter('pdf_Higgs_qqbar', 'lnN')
    pdfttH = rl.NuisanceParameter('pdf_Higgs_ttH', 'lnN')
    pdfggHH = rl.NuisanceParameter('pdf_Higgs_ggHH', 'lnN')
    pdfqqHH = rl.NuisanceParameter('pdf_Higgs_qqHH', 'lnN')
    qcdScaleVH = rl.NuisanceParameter('QCDscale_VH', 'lnN')
    qcdScalettH = rl.NuisanceParameter('QCDscale_ttH', 'lnN')
    qcdScaleqqHH = rl.NuisanceParameter('QCDscale_qqHH', 'lnN')
    alphaS = rl.NuisanceParameter('alpha_s', 'lnN')
    fsrothers = rl.NuisanceParameter('CMS_bbbb_boosted_ggf_ps_fsr_others', 'lnN')
    isrothers = rl.NuisanceParameter('CMS_bbbb_boosted_ggf_ps_isr_others', 'lnN')
    if not include_ac:
        thu_hh = rl.NuisanceParameter('THU_SMHH', 'lnN')

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

    passTempl = get_hist(upfile, 'histJet2MassBlind_'+passBinName+'_QCD', obs=msd)
    fitfailTempl = get_hist(upfile, 'histJet2Massfit_fail_QCD', obs=msd)

    passCh.setObservation(passTempl[:-1])
    fitfailCh.setObservation(fitfailTempl[:-1])
    qcdpass = passCh.getObservation().sum()
    qcdfitfail = fitfailCh.getObservation().sum()

    qcdeffpass = qcdpass / qcdfitfail

    # transfer factor
    tf_dataResidual = rl.BernsteinPoly("CMS_bbbb_boosted_ggf_tf_dataResidual_"+passBinName, (nDataTF,), ['msd'], limits=(-20, 20))
    tf_dataResidual_params = tf_dataResidual(msdscaled)
    tf_params_pass = qcdeffpass * tf_dataResidual_params

    # qcd params
    qcdparams = np.array([rl.IndependentParameter('CMS_bbbb_boosted_ggf_qcdparam_msdbin%d' % i, 0) for i in range(msd.nbins)])

    # dictionary of shape systematics -> name in cards
    systs = OrderedDict([
        ('mHHTHunc', 'CMS_bbbb_boosted_ggf_mHHTHunc'),
        ('FSRPartonShower', 'ps_fsr'),
        ('ISRPartonShower', 'ps_isr'),
        ('ggHHPDFacc', 'CMS_bbbb_boosted_ggf_ggHHPDFacc'),
        ('ggHHQCDacc', 'CMS_bbbb_boosted_ggf_ggHHQCDacc'),
        ('othersQCD', 'CMS_bbbb_boosted_ggf_othersQCD'),
        ('pileupWeight2016', 'CMS_pileup_2016'),
        ('pileupWeight2017', 'CMS_pileup_2017'),
        ('pileupWeight2018', 'CMS_pileup_2018'),
        ('JER2016', 'CMS_res_j_2016'),
        ('JER2017', 'CMS_res_j_2017'),
        ('JER2018', 'CMS_res_j_2018'),
        ('JES_Abs', 'CMS_scale_j_Abs'),
        ('JES_Abs_2016', 'CMS_scale_j_Abs_2016'),
        ('JES_Abs_2017', 'CMS_scale_j_Abs_2017'),
        ('JES_Abs_2018', 'CMS_scale_j_Abs_2018'),
        ('JES_BBEC1', 'CMS_scale_j_BBEC1'),
        ('JES_BBEC1_2016', 'CMS_scale_j_BBEC1_2016'),
        ('JES_BBEC1_2017', 'CMS_scale_j_BBEC1_2017'),
        ('JES_BBEC1_2018', 'CMS_scale_j_BBEC1_2018'),
        ('JES_EC2', 'CMS_scale_j_EC2'),
        ('JES_EC2_2016', 'CMS_scale_j_EC2_2016'),
        ('JES_EC2_2017', 'CMS_scale_j_EC2_2017'),
        ('JES_EC2_2018', 'CMS_scale_j_EC2_2018'),
        ('JES_FlavQCD', 'CMS_scale_j_FlavQCD'),
        ('JES_HF', 'CMS_scale_j_HF'),
        ('JES_HF_2016', 'CMS_scale_j_HF_2016'),
        ('JES_HF_2017', 'CMS_scale_j_HF_2017'),
        ('JES_HF_2018', 'CMS_scale_j_HF_2018'),
        ('JES_RelBal', 'CMS_scale_j_RelBal'),
        ('JES_RelSample_2016', 'CMS_scale_j_RelSample_2016'),
        ('JES_RelSample_2017', 'CMS_scale_j_RelSample_2017'),
        ('JES_RelSample_2018', 'CMS_scale_j_RelSample_2018'),
        ('JMS2016', 'CMS_bbbb_boosted_ggf_jms_2016'),
        ('JMS2017', 'CMS_bbbb_boosted_ggf_jms_2017'),
        ('JMS2018', 'CMS_bbbb_boosted_ggf_jms_2018'),
        ('JMR2016', 'CMS_bbbb_boosted_ggf_jmr_2016'),
        ('JMR2017', 'CMS_bbbb_boosted_ggf_jmr_2017'),
        ('JMR2018', 'CMS_bbbb_boosted_ggf_jmr_2018'),
        ('ttbarBin1Jet2PNetCut', 'CMS_bbbb_boosted_ggf_ttbarBin1Jet2PNetCut'),
        ('ttJetsCorr', 'CMS_bbbb_boosted_ggf_ttJetsCorr'),
        ('BDTShape', 'CMS_bbbb_boosted_ggf_ttJetsBDTShape'),
        ('PNetShape', 'CMS_bbbb_boosted_ggf_ttJetsPNetShape'),
        ('PNetHbbScaleFactors', 'CMS_bbbb_boosted_ggf_PNetHbbScaleFactors_uncorrelated'),
        ('triggerEffSF', 'CMS_bbbb_boosted_ggf_triggerEffSF_uncorrelated'),
        ('trigCorrHH2016', 'CMS_bbbb_boosted_ggf_trigCorrHH2016'),
        ('trigCorrHH2017', 'CMS_bbbb_boosted_ggf_trigCorrHH2017'),
        ('trigCorrHH2018', 'CMS_bbbb_boosted_ggf_trigCorrHH2018'),
    ])

    # build actual fit model now
    model = rl.Model("HHModel")
    for region in regions:
        logging.info('starting region: %s' % region)
        ch = rl.Channel(region)
        model.addChannel(ch)

        if region == 'pass'+passBinName:
            catn = 'Blind_'+passBinName
        elif region == 'SR'+passBinName:
            catn = '_'+passBinName
        elif region == 'fit'+failBinName:
            catn = 'fit_'+failBinName
        else:
            catn = 'Blind_'+failBinName

        # dictionary of name in datacards -> name in ROOT file
        templateNames = OrderedDict([
            ('ttbar', 'histJet2Mass'+catn+'_TTJets'),
            ('VH_hbb', 'histJet2Mass'+catn+'_VH'),
            ('ttH_hbb', 'histJet2Mass'+catn+'_ttH'),
            ('bbbb_boosted_ggf_others', 'histJet2Mass'+catn+'_others'),
            ('bbbb_boosted_ggf_qcd_datadriven', 'histJet2Mass'+catn+'_QCD'),
            ('data', 'histJet2Mass'+catn+'_Data'),
            ('ggHH_kl_1_kt_1_hbbhbb', 'histJet2Mass'+catn+'_ggHH_kl_1_kt_1_boost4b'),
            ('qqHH_CV_1_C2V_1_kl_1_hbbhbb', 'histJet2Mass'+catn+'_qqHH_CV_1_C2V_1_kl_1_boost4b'),
        ])
        ac_signals = OrderedDict()
        if include_ac:
            ac_signals = OrderedDict([
                ('ggHH_kl_2p45_kt_1_hbbhbb', 'histJet2Mass'+catn+'_ggHH_kl_2p45_kt_1_boost4b'),
                ('ggHH_kl_5_kt_1_hbbhbb', 'histJet2Mass'+catn+'_ggHH_kl_5_kt_1_boost4b'),
                ('ggHH_kl_0_kt_1_hbbhbb', 'histJet2Mass'+catn+'_ggHH_kl_0_kt_1_boost4b'),
                ('qqHH_CV_1_C2V_0_kl_1_hbbhbb', 'histJet2Mass'+catn+'_qqHH_CV_1_C2V_0_kl_1_boost4b'),
                ('qqHH_CV_1p5_C2V_1_kl_1_hbbhbb', 'histJet2Mass'+catn+'_qqHH_CV_1p5_C2V_1_kl_1_boost4b'),
                ('qqHH_CV_1_C2V_1_kl_2_hbbhbb', 'histJet2Mass'+catn+'_qqHH_CV_1_C2V_1_kl_2_boost4b'),
                ('qqHH_CV_1_C2V_2_kl_1_hbbhbb', 'histJet2Mass'+catn+'_qqHH_CV_1_C2V_2_kl_1_boost4b'),
                ('qqHH_CV_1_C2V_1_kl_0_hbbhbb', 'histJet2Mass'+catn+'_qqHH_CV_1_C2V_1_kl_0_boost4b'),
                ('qqHH_CV_0p5_C2V_1_kl_1_hbbhbb', 'histJet2Mass'+catn+'_qqHH_CV_0p5_C2V_1_kl_1_boost4b'),
            ])
            templateNames.update(ac_signals)

        templates = {}
        for temp in templateNames:
            templates[temp] = get_hist(upfile, templateNames[temp], obs=msd)

        if adjust_posdef_yields:
            templates_posdef = {}
            # requires python3 and cvxpy
            if sys.version_info.major == 3:
                from bpe import BasisPointExpansion
                from adjust_to_posdef import ggHH_points, qqHH_points, plot_shape
                channel = "_hbbhbb"
                # get qqHH points
                qqHHproc = BasisPointExpansion(3)
                ggHHproc = BasisPointExpansion(2)
                newpts = {}
                newerrs = {}
                for HHproc, HH_points in zip([ggHHproc, qqHHproc], [ggHH_points, qqHH_points]):
                    for name, c in HH_points.items():
                        shape = np.clip(templates[name + channel][0], 0, None)
                        err = np.sqrt(templates[name + channel][3])
                        # set 0 bin error to something non0
                        err[err == 0] = err[err.nonzero()].min()
                        logging.debug(name + channel)
                        logging.debug("shape: {shape}".format(shape=shape))
                        logging.debug("err: {err}".format(err=err))
                        HHproc.add_point(c, shape, err)
                    # fit HH points with SCS
                    HHproc.solve("scs", tol=1e-9)
                    # get new HH points
                    for name, c in HH_points.items():
                        newshape = HHproc(c)
                        shape = templates[name + channel][0]
                        edges = templates[name + channel][1]
                        obs_name = templates[name + channel][2]
                        err = np.sqrt(templates[name + channel][3])
                        # set error to 100% if shape orignally 0 and now not
                        newerr = np.copy(err)
                        newerr[(newshape > 0) & (newerr == 0)] = newshape[(newshape > 0) & (newerr == 0)]
                        templates_posdef[name + channel] = (newshape, edges, obs_name, np.square(newerr))
                        plot_shape(shape, newshape, err, newerr, name+"_"+region)
                        newpts[name + channel] = newshape
                        newerrs[name + channel] = newerr
                np.savez("newshapes_{}.npz".format(region), **newpts)
                np.savez("newerrors_{}.npz".format(region), **newerrs)
            else:
                if not (os.path.exists("newshapes_{}.npz".format(region)) and os.path.exists("newerrors_{}.npz".format(region))):
                    raise RuntimeError("Run script in python3 first to get shapes and errors")
                newpts = dict(np.load("newshapes_{}.npz".format(region)))
                newerrs = dict(np.load("newerrors_{}.npz".format(region)))
                for temp in templateNames:
                    if "HH" in temp:
                        newshape = newpts[temp]
                        newerr = newerrs[temp]
                        edges = templates[temp][1]
                        obs_name = templates[temp][2]
                        templates_posdef[temp] = (newshape, edges, obs_name, np.square(newerr))

        syst_param_array = []
        for syst in systs:
            syst_param_array.append(rl.NuisanceParameter(systs[syst], 'shape'))

        sNames = [proc for proc in templates.keys() if proc not in ['bbbb_boosted_ggf_qcd_datadriven', 'data']]

        for sName in sNames:
            logging.info('get templates for: %s' % sName)
            # get templates
            templ = templates[sName]
            # don't allow them to go negative
            valuesNominal = np.maximum(templ[0], 0.)
            templ = (valuesNominal, templ[1], templ[2], templ[3])
            stype = rl.Sample.SIGNAL if 'HH' in sName else rl.Sample.BACKGROUND
            if adjust_posdef_yields and "HH" in sName:
                # use posdef as nominal, but keep original to get relative changes to systematics
                templ_posdef = templates_posdef[sName]
                sample = rl.TemplateSample(ch.name + '_' + sName, stype, templ_posdef)
            else:
                sample = rl.TemplateSample(ch.name + '_' + sName, stype, templ)
            sample.setParamEffect(lumi_13TeV_2016, 1.01 ** (lumi_16 / lumi_run2))
            sample.setParamEffect(lumi_13TeV_2017, 1.02 ** (lumi_17 / lumi_run2))
            sample.setParamEffect(lumi_13TeV_2018, 1.015 ** (lumi_18 / lumi_run2))
            sample.setParamEffect(
                lumi_13TeV_correlated,
                1.02 ** (lumi_18 / lumi_run2) * 1.009 ** (lumi_17 / lumi_run2) * 1.006 ** (lumi_16 / lumi_run2)
             )
            sample.setParamEffect(
                lumi_13TeV_1718,
                1.006 ** (lumi_17 / lumi_run2) * 1.002 ** (lumi_18 / lumi_run2)
            )
            if not include_ac:
                if sName == "ggHH_kl_1_kt_1_hbbhbb":
                    sample.setParamEffect(thu_hh, 1.0556, 0.7822)

            if sName == "bbbb_boosted_ggf_others":
                if "Bin1" in region:
                    sample.setParamEffect(fsrothers, 1.06, 0.82)
                    sample.setParamEffect(isrothers, 1.05, 0.94)
                elif "Bin2" in region:
                    sample.setParamEffect(fsrothers, 1.02, 0.90)
                    sample.setParamEffect(isrothers, 1.07, 0.93)
                elif "Bin3" in region:
                    sample.setParamEffect(fsrothers, 1.02, 0.91)
                    sample.setParamEffect(isrothers, 1.06, 0.93)
                elif "fail" in region:
                    sample.setParamEffect(fsrothers, 1.05, 0.92)
                    sample.setParamEffect(isrothers, 1.05, 0.94)

            if sName == "ttbar" and "Bin1" in region:
                if region == "passBin1":
                    sample.setParamEffect(ttbarBin1MCstats, 1.215)
                elif region == "SRBin1":
                    sample.setParamEffect(ttbarBin1MCstats, 1.187)

            if ("VH" in sName) or ("ttH" in sName):
                sample.setParamEffect(PNetHbbScaleFactorssyst, 1.04)
            elif "HH" in sName:
                sample.setParamEffect(PNetHbbScaleFactorssyst, 1.0816)

            if "hbbhbb" in sName:
                sample.setParamEffect(brHbb, 1.0248, 0.9748)
            elif "hbb" in sName:
                sample.setParamEffect(brHbb, 1.0124, 0.9874)

            if "ttH" in sName:
                sample.setParamEffect(pdfttH, 1.030)
                sample.setParamEffect(qcdScalettH, 1.058, 0.908)
                sample.setParamEffect(alphaS, 1.020)
            elif "VH" in sName:
                sample.setParamEffect(pdfqqbar, 1.0154)
                sample.setParamEffect(qcdScaleVH, 1.0179, 0.9840)
                sample.setParamEffect(alphaS, 1.009)
            elif "ggHH" in sName:
                sample.setParamEffect(pdfggHH, 1.030)
            elif "qqHH" in sName:
                sample.setParamEffect(pdfqqHH, 1.021)
                sample.setParamEffect(qcdScaleqqHH, 1.0003, 0.9996)

            # shape systematics
            mask = (valuesNominal > 0)
            errorsNominal = np.ones_like(valuesNominal)
            errorsNominal[mask] = 1. + np.sqrt(templ[3][mask])/valuesNominal[mask]

            # set mc stat uncs
            logging.info('setting autoMCStats for %s in %s' % (sName, region))
            logging.debug('nominal   : {nominal}'.format(nominal=valuesNominal))
            logging.debug('error     : {errors}'.format(errors=errorsNominal))
            sample.autoMCStats()

            for isyst, syst in enumerate(systs):
                # negligible uncertainty
                if 'JES_EC2' in syst or 'JES_HF' in syst:
                    continue
                # add some easy skips
                if (sName != 'ttbar') and (syst in ['ttJetsCorr', 'BDTShape', 'PNetShape']):
                    continue
                if ((sName != 'ttbar') or ('Bin1' not in region)) and (syst == 'ttbarBin1Jet2PNetCut'):
                    continue
                if ('ggHH' not in sName) and (syst in ['ggHHPDFacc', 'ggHHQCDacc', 'mHHTHunc']):
                    continue
                if ('others' not in sName) and (syst == 'othersQCD'):
                    continue
                if ('hbb' not in sName) and (syst == 'PNetHbbScaleFactors'):
                    continue
                if ('HH' not in sName) and (syst in ['trigCorrHH2016', 'trigCorrHH2017', 'trigCorrHH2018']):
                    continue
                logging.info('setting shape effect %s for %s in %s' % (syst, sName, region))
                valuesUp = get_hist(upfile, '%s_%sUp' % (templateNames[sName], syst), obs=msd)[0]
                valuesDown = get_hist(upfile, '%s_%sDown' % (templateNames[sName], syst), obs=msd)[0]
                effectUp = np.ones_like(valuesNominal)
                effectDown = np.ones_like(valuesNominal)
                maskUp = (valuesUp >= 0)
                maskDown = (valuesDown >= 0)
                effectUp[mask & maskUp] = valuesUp[mask & maskUp]/valuesNominal[mask & maskUp]
                effectDown[mask & maskDown] = valuesDown[mask & maskDown]/valuesNominal[mask & maskDown]
                # do shape checks
                normUp = np.sum(valuesUp)
                normDown = np.sum(valuesDown)
                normNominal = np.sum(valuesNominal)
                probUp = valuesUp/normUp
                probDown = valuesDown/normDown
                probNominal = valuesNominal/normNominal
                shapeEffectUp = np.sum(np.abs(probUp - probNominal)/(np.abs(probUp)+np.abs(probNominal)))
                shapeEffectDown = np.sum(np.abs(probDown - probNominal)/(np.abs(probDown)+np.abs(probNominal)))
                logger = logging.getLogger("validate_shapes_{}_{}_{}".format(region, sName, syst))
                valid = True
                if np.allclose(effectUp, 1.) and np.allclose(effectDown, 1.):
                    valid = False
                    logger.warning("No shape effect")
                elif np.allclose(effectUp, effectDown):
                    valid = False
                    logger.warning("Up is the same as Down, but different from nominal")
                elif np.allclose(effectUp, 1.) or np.allclose(effectDown, 1.):
                    valid = False
                    logger.warning("Up or Down is the same as nominal (one-sided)")
                elif shapeEffectUp < 0.001 and shapeEffectDown < 0.001:
                    valid = False
                    logger.warning("No genuine shape effect (just norm)")
                elif (normUp > normNominal and normDown > normNominal) or (normUp < normNominal and normDown < normNominal):
                    valid = False
                    logger.warning("Up and Down vary norm in the same direction")
                if valid:
                    logger.info("Shapes are valid")
                logging.debug("nominal   : {nominal}".format(nominal=valuesNominal))
                logging.debug("effectUp  : {effectUp}".format(effectUp=effectUp))
                logging.debug("effectDown: {effectDown}".format(effectDown=effectDown))
                sample.setParamEffect(syst_param_array[isyst], effectUp, effectDown)
            ch.addSample(sample)

        # data observed
        yields = templates['data'][0]
        data_obs = (yields, msd.binning, msd.name)
        ch.setObservation(data_obs)

    for passChName, failChName in regionPairs:
        logging.info('setting transfer factor for pass region %s, fail region %s' % (passChName, failChName))
        failCh = model[failChName]
        passCh = model[passChName]

        # sideband fail
        initial_qcd = failCh.getObservation().astype(float)  # was integer, and numpy complained about subtracting float from it
        for sample in failCh:
            if sample._name in [failChName+"_"+signalName for signalName in ac_signals.keys()]:
                continue
            logging.debug('subtracting %s from qcd' % sample._name)
            initial_qcd -= sample.getExpectation(nominal=True)
        if np.any(initial_qcd < 0.):
            raise ValueError("initial_qcd negative for some bins..", initial_qcd)
        sigmascale = 10  # to scale the deviation from initial
        scaledparams = initial_qcd * (1 + sigmascale/np.maximum(1., np.sqrt(initial_qcd)))**qcdparams

        # add samples
        fail_qcd = rl.ParametericSample(failChName+'_bbbb_boosted_ggf_qcd_datadriven', rl.Sample.BACKGROUND, msd, scaledparams)
        failCh.addSample(fail_qcd)

        pass_qcd = rl.TransferFactorSample(passChName+'_bbbb_boosted_ggf_qcd_datadriven', rl.Sample.BACKGROUND, tf_params_pass, fail_qcd)
        passCh.addSample(pass_qcd)

    with open(os.path.join(str(carddir), 'HHModel.pkl'), "wb") as fout:
        pickle.dump(model, fout, 2)  # use python 2 compatible protocol

    logging.info('rendering combine model')
    model.renderCombine(os.path.join(str(carddir), 'HHModel'))


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--inputfile', default='HHTo4BPlots_Run2_BDTv8p2_0311_syst_Trigv0.root', type=str, dest='inputfile', help='input ROOT file')
    parser.add_argument('--carddir', default='cards', type=str, dest='carddir', help='output card directory')
    parser.add_argument('--nbins', default=17, type=int, dest='nbins', help='number of bins')
    parser.add_argument('--nMCTF', default=0, type=int, dest='nMCTF', help='order of polynomial for TF from MC')
    parser.add_argument('--nDataTF', default=2, type=int, dest='nDataTF', help='order of polynomial for TF from Data')
    parser.add_argument('--passBinName', default='Bin1', type=str, choices=['Bin1', 'Bin2', 'Bin3'], help='pass bin name')
    parser.add_argument('--blinded', action='store_true', help='run on data on SR')
    args = parser.parse_args()
    if not os.path.exists(args.carddir):
        os.mkdir(args.carddir)
    create_datacard(args.inputfile, args.carddir, args.nbins, args.nMCTF, args.nDataTF, args.passBinName, "fail", args.blinded)
