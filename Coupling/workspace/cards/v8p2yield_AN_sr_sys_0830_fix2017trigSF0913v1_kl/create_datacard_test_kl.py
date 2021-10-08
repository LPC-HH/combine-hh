from __future__ import print_function, division
import sys
import os
import rhalphalib as rl
import numpy as np
import scipy.stats
import pickle
import uproot
import ROOT
rl.util.install_roofit_helpers()
rl.ParametericSample.PreferRooParametricHist = False

def get_hist(inputfile, name, obs):
    upfile = uproot.open(inputfile)
    hist_values = upfile[name].values()
    hist_edges = upfile[name].axis().edges()
    hist_uncs = upfile[name].variances()
    if obs.binning != hist_edges:
        # rebin (assumes new bins are a subset of existing bins)
        edge_mask = np.in1d(hist_edges,obs.binning)
        hist_mask = np.logical_and(edge_mask[0:-1], edge_mask[1:])
        hist_values = hist_values[hist_mask]
        hist_edges = hist_edges[edge_mask]
        hist_uncs = hist_uncs[hist_mask]
    return (hist_values, hist_edges, obs.name, hist_uncs)

def create_datacard(inputfile, carddir, nbins, nMCTF, nDataTF, passBinName, failBinName):
    ttbarBin1MCstats = rl.NuisanceParameter('ttbarBin1_yieldMCStats', 'lnN')
    lumi = rl.NuisanceParameter('CMS_lumi', 'lnN')
    #ttnorm = rl.NuisanceParameter('ttnorm', 'lnN')
    trigSF = rl.NuisanceParameter('triggerEffSF_correlated', 'lnN')
    PNetHbbScaleFactorssyst = rl.NuisanceParameter('PNetHbbScaleFactors_correlated', 'lnN')

    msdbins = np.linspace(50, nbins*10.0+50.0, nbins+1)
    msd = rl.Observable('msd', msdbins)
    msdpts = msdbins[:-1] + 0.5 * np.diff(msdbins)
    msdscaled = (msdpts - 50.)/(10.0*nbins)

    # Build qcd MC pass+fail model and fit to polynomial
    qcdmodel = rl.Model('qcdmodel')
    qcdpass, qcdfitfail = 0., 0.
    #failCh = rl.Channel('failqcdmodel')
    passCh = rl.Channel('passqcdmodel')
    #srfailCh = rl.Channel('SRfailqcdmodel')
    #srpassCh = rl.Channel('SRqcdmodel')
    fitfailCh = rl.Channel('fitfailqcdmodel')
    qcdmodel.addChannel(fitfailCh)
    qcdmodel.addChannel(passCh)
    #qcdmodel.addChannel(srpassCh)
    
    # pseudodata MC template
    #failTempl = get_hist(inputfile, 'histJet2MassBlind_'+failBinName+'_QCD', obs=msd)
    passTempl = get_hist(inputfile, 'histJet2MassBlind_'+passBinName+'_QCD', obs=msd)
    #srfailTempl = get_hist(inputfile, 'histJet2MassSR_'+failBinName+'_QCD', obs=msd)
    #srpassTempl = get_hist(inputfile, 'histJet2MassSR_'+passBinName+'_QCD', obs=msd)
    fitfailTempl = get_hist(inputfile, 'histJet2Massfit_fail_QCD', obs=msd)
    
    #failCh.setObservation(failTempl[:-1])
    passCh.setObservation(passTempl[:-1])
    
    #srfailCh.setObservation(srfailTempl[:-1])
    #srpassCh.setObservation(srpassTempl[:-1])
    
    fitfailCh.setObservation(fitfailTempl[:-1])
    
    qcdpass = passCh.getObservation().sum()
    qcdfitfail = fitfailCh.getObservation().sum()
    qcdeffpass = qcdpass / qcdfitfail
    
    #transfer factor
    tf_dataResidual = rl.BernsteinPoly("tf_dataResidual_"+passBinName, (nDataTF,), ['msd'], limits=(-20, 20))
    #tf_dataResidual = rl.BernsteinPoly("tf_dataResidual", (nDataTF,), ['msd'], limits=(0, 10))
    tf_dataResidual_params = tf_dataResidual(msdscaled)
    #tf_params = qcdeff * tf_MCtempl_params_final * tf_dataResidual_params
    tf_params_pass = qcdeffpass * tf_dataResidual_params
    #tf_params_sr = qcdeffsr * tf_dataResidual_params
    
    # build actual fit model now
    model = rl.Model("HHModel")
    for region in ['pass'+passBinName, 'fail','SR'+passBinName, 'fitfail']:
        #print("region ",region)
        ch = rl.Channel(region)
        model.addChannel(ch)

        isPass = region == 'pass'+passBinName
        isSR = region=='SR'+passBinName
        isfitfail = region=='fitfail'
        
        catn = 'Blind_'+passBinName
        if not isPass:
            if isSR:
                catn = "_"+passBinName
            elif isfitfail:
                catn = 'fit_'+failBinName    
            else:
                catn = 'Blind_'+failBinName               
            
        templates = {
            'TTJets': get_hist(inputfile, 'histJet2Mass'+catn+'_TTJets', obs=msd),
            'ggHH_kl_1_kt_1_boost4b': get_hist(inputfile, 'histJet2Mass'+catn+'_ggHH_kl_1_kt_1_boost4b', obs=msd),
            'ggHH_kl_2p45_kt_1_boost4b': get_hist(inputfile, 'histJet2Mass'+catn+'_ggHH_kl_2p45_kt_1_boost4b', obs=msd),
            'ggHH_kl_5_kt_1_boost4b': get_hist(inputfile, 'histJet2Mass'+catn+'_ggHH_kl_5_kt_1_boost4b', obs=msd),
            'qqHH_CV_1_C2V_1_kl_1_boost4b': get_hist(inputfile, 'histJet2Mass'+catn+'_qqHH_CV_1_C2V_1_kl_1_boost4b', obs=msd),
            'qqHH_CV_1_C2V_0_kl_1_boost4b': get_hist(inputfile, 'histJet2Mass'+catn+'_qqHH_CV_1_C2V_0_kl_1_boost4b', obs=msd),
            'qqHH_CV_1p5_C2V_1_kl_1_boost4b': get_hist(inputfile, 'histJet2Mass'+catn+'_qqHH_CV_1p5_C2V_1_kl_1_boost4b', obs=msd),
            'qqHH_CV_1_C2V_1_kl_2_boost4b': get_hist(inputfile, 'histJet2Mass'+catn+'_qqHH_CV_1_C2V_1_kl_2_boost4b', obs=msd),
            'qqHH_CV_1_C2V_2_kl_1_boost4b': get_hist(inputfile, 'histJet2Mass'+catn+'_qqHH_CV_1_C2V_2_kl_1_boost4b', obs=msd),
            'qqHH_CV_1_C2V_1_kl_0_boost4b': get_hist(inputfile, 'histJet2Mass'+catn+'_qqHH_CV_1_C2V_1_kl_0_boost4b', obs=msd),
            'VH': get_hist(inputfile, 'histJet2Mass'+catn+'_VH', obs=msd),
            'ttH': get_hist(inputfile, 'histJet2Mass'+catn+'_ttH', obs=msd),
            'others': get_hist(inputfile, 'histJet2Mass'+catn+'_others', obs=msd),
            'QCD': get_hist(inputfile, 'histJet2Mass'+catn+'_QCD', obs=msd),
            'Data': get_hist(inputfile, 'histJet2Mass'+catn+'_Data', obs=msd),
        }
       
        systs = ['ttbarBin1Jet2PNetCut', 'FSRPartonShower', 'ISRPartonShower', 'ggHHPDFacc', 'ggHHQCDacc', 'pileupWeight', 'JER', 'JES', 'JMS', 'JMR', 'ttJetsCorr', 'BDTShape', 'PNetShape', 'PNetHbbScaleFactors', 'triggerEffSF'] 
        #systs = ['pileupWeight', 'JES', 'JMS', 'JMR', 'ttJetsCorr', 'BDTShape', 'PNetShape', 'PNetHbbScaleFactors']#, 'triggerEffSF']
        systs_name_in_cards = ['ttbarBin1Jet2PNetCut', 'FSRPartonShower', 'ISRPartonShower', 'ggHHPDFacc', 'ggHHQCDacc', 'CMS_pileup', 'CMS_JER', 'CMS_JES', 'CMS_JMS', 'CMS_JMR', 'ttJetsCorr', 'ttJetsBDTShape', 'ttJetsPNetShape', 'PNetHbbScaleFactors_uncorrelated', 'triggerEffSF_uncorrelated'] 
        #systs_name_in_cards = ['CMS_pileup', 'CMS_JES', 'CMS_JMS', 'CMS_JMR', 'ttJetsCorr', 'ttJetsBDTShape', 'ttJetsPNetShape', 'PNetHbbScaleFactors_uncorrelated'] #, 'triggerEffSF_uncorrelated']
        
        syst_param_array = []
        for i in range(len(systs)):
            syst_param_array.append(rl.NuisanceParameter(systs_name_in_cards[i], 'shape'))
            
        #print("syst_param_array",syst_param_array)
        
        for sName in ['TTJets', 'ggHH_kl_1_kt_1_boost4b','ggHH_kl_2p45_kt_1_boost4b', 'ggHH_kl_5_kt_1_boost4b',
        'qqHH_CV_1_C2V_1_kl_1_boost4b','qqHH_CV_1_C2V_0_kl_1_boost4b', 'qqHH_CV_1p5_C2V_1_kl_1_boost4b', 'qqHH_CV_1_C2V_1_kl_2_boost4b',
        'qqHH_CV_1_C2V_2_kl_1_boost4b', 'qqHH_CV_1_C2V_1_kl_0_boost4b','VH', 'ttH', 'others']:
            
            #print("sName ",sName)
            # get templates
            templ = templates[sName]
            stype = rl.Sample.SIGNAL if 'HH' in sName else rl.Sample.BACKGROUND
            sample = rl.TemplateSample(ch.name + '_' + sName, stype, templ)
            
            sample.setParamEffect(lumi, 1.016)
            sample.setParamEffect(trigSF, 1.04)   
            
            if ("TTJets"==sName and "Bin1" in region ):
                #print("sName and ttbar yield Bin1 MC stats unc ", sName)
                if ("passBin1" == region):
                    #sample.setParamEffect(ttbarBin1MCstats, 1.256)
                    sample.setParamEffect(ttbarBin1MCstats, 1.215)
                elif ("SRBin1" == region):
		    #sample.setParamEffect(ttbarBin1MCstats, 1.240)
                    sample.setParamEffect(ttbarBin1MCstats, 1.187)

            if ("VH" in sName) or ("ttH" in sName) : 
                #print("sName and PNetSF 5%: ",sName)
                sample.setParamEffect(PNetHbbScaleFactorssyst, 1.04)
            elif "HH" in sName:
                #print("sName and PNetSF 10%: ",sName)
                sample.setParamEffect(PNetHbbScaleFactorssyst, 1.0816)

            # set mc stat uncs
            sample.autoMCStats()

            #shape systematics
            valuesNominal =  templ[0]
            
            isyst = 0
            for syst in systs:
                #print("sName systname ",sName,syst)
                valuesUp = get_hist(inputfile, 'histJet2Mass'+catn+'_%s_%sUp'%(sName, syst), obs=msd)[0]
                valuesDown = get_hist(inputfile, 'histJet2Mass'+catn+'_%s_%sDown'%(sName, syst), obs=msd)[0]
                #print("valuesUp: ",valuesUp)
                #print('histJet2Mass'+catn+'_%s_%sUp'%(sName, syst))
                #print("valuesDown: ",valuesDown)
                #print('histJet2Mass'+catn+'_%s_%sDown'%(sName, syst))
                effectUp = np.ones_like(valuesNominal)
                effectDown = np.ones_like(valuesNominal)
                for i in range(len(valuesNominal)):
                    if valuesNominal[i] >  0.:
                        effectUp[i]   = valuesUp[i]/valuesNominal[i]
                        effectDown[i]   = valuesDown[i]/valuesNominal[i]
                sample.setParamEffect(syst_param_array[isyst], effectUp, effectDown)
                isyst = isyst + 1
            ch.addSample(sample)

        # make up a data_obs by summing the MC templates above
        #yields = sum(tpl[0] for tpl in templates.values())
        yields = templates['Data'][0]
        data_obs = (yields, msd.binning, msd.name)
        ch.setObservation(data_obs)        

    failCh = model['fail']
    passCh = model['pass'+passBinName]
    
    #srfailCh = model['SRfail']
    srCh = model['SR'+passBinName]
    
    fitfailCh = model['fitfail']

    qcdparams = np.array([rl.IndependentParameter('qcdparam_msdbin%d'%i, 0) for i in range(msd.nbins)])

    #sideband fail
    initial_qcd = failCh.getObservation().astype(float)  # was integer, and numpy complained about subtracting float from it
    for sample in failCh:
        initial_qcd -= sample.getExpectation(nominal=True)
    if np.any(initial_qcd < 0.):
        raise ValueError("initial_qcd negative for some bins..", initial_qcd)
    sigmascale = 10  # to scale the deviation from initial
    scaledparams = initial_qcd * (1 + sigmascale/np.maximum(1., np.sqrt(initial_qcd)))**qcdparams

    #fit region fail
    initial_qcd_fit = fitfailCh.getObservation().astype(float)  # was integer, and numpy complained about subtracting float from it
    for sample in fitfailCh:
        initial_qcd_fit -= sample.getExpectation(nominal=True)
    if np.any(initial_qcd_fit < 0.):
        raise ValueError("initial_qcd_fit negative for some bins..", initial_qcd_fit)    
    scaledparams_fit = initial_qcd_fit * (1 + sigmascale/np.maximum(1., np.sqrt(initial_qcd_fit)))**qcdparams
       
    fail_qcd = rl.ParametericSample('fail_qcd', rl.Sample.BACKGROUND, msd, scaledparams)
    failCh.addSample(fail_qcd)
        
    #name: channel name _ proc name
    #fail_qcd_sr = rl.ParametericSample('SRfail_qcd', rl.Sample.BACKGROUND, msd, scaledparams_fit)
    #srfailCh.addSample(fail_qcd_sr)
    
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
    parser.add_argument('--carddir', default='cards', type=str, dest='carddir', help= 'output card directory')
    parser.add_argument('--nbins', default=17, type=int, dest='nbins', help= 'number of bins')
    parser.add_argument('--nMCTF', default=0, type=int, dest='nMCTF', help= 'order of polynomial for TF from MC')
    parser.add_argument('--nDataTF', default=2, type=int, dest='nDataTF', help= 'order of polynomial for TF from Data')
    
    args = parser.parse_args()
    for fitbin in ["Bin1", "Bin2", "Bin3"]:
        os.system("rm -rf cards_"+fitbin)
        os.system("mkdir cards_"+fitbin)
    
    create_datacard(args.inputfile, "cards_Bin1", args.nbins, 0, 0, "Bin1", "fail")
    create_datacard(args.inputfile, "cards_Bin2", args.nbins, 0, 0, "Bin2", "fail")
    create_datacard(args.inputfile, "cards_Bin3", args.nbins, 0, 0, "Bin3", "fail")
