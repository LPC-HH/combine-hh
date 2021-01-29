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

    lumi = rl.NuisanceParameter('CMS_lumi', 'lnN')

    msdbins = np.linspace(50, nbins*10.0+50.0, nbins+1)
    msd = rl.Observable('msd', msdbins)
    msdpts = msdbins[:-1] + 0.5 * np.diff(msdbins)
    msdscaled = (msdpts - 50.)/(10.0*nbins)

    # Build qcd MC pass+fail model and fit to polynomial
    qcdmodel = rl.Model('qcdmodel')
    qcdpass, qcdfail, qcdsr = 0., 0., 0.
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
    
    qcdfail = failCh.getObservation().sum()
    qcdpass = passCh.getObservation().sum()
    
    qcdsrfail = srfailCh.getObservation().sum()
    qcdsrpass = srpassCh.getObservation().sum()
    
    qcdeffpass = qcdpass / qcdsrfail
    #qcdeffsr = qcdsrpass / qcdsrfail
    qcdeffsr = qcdpass / qcdsrfail

    #tf_MCtempl = rl.BernsteinPoly("tf_MCtempl", (nMCTF,), ['msd'], limits=(0, 10))
    #tf_MCtempl_params = qcdeff * tf_MCtempl(msdscaled)
    
    #failCh = qcdmodel['fail']
    #passCh = qcdmodel['pass']
    #failObs = failCh.getObservation()
    #qcdparams = np.array([rl.IndependentParameter('qcdparam_msdbin%d'%i, 0) for i in range(msd.nbins)])
    #sigmascale = 10.
    #scaledparams = failObs * (1 + sigmascale/np.maximum(1., np.sqrt(failObs)))**qcdparams
    #fail_qcd = rl.ParametericSample('fail_qcd', rl.Sample.BACKGROUND, msd, scaledparams)
    #failCh.addSample(fail_qcd)
    #pass_qcd = rl.TransferFactorSample('pass_qcd', rl.Sample.BACKGROUND, tf_MCtempl_params, fail_qcd)
    #passCh.addSample(pass_qcd)
    
    #qcdfit_ws = ROOT.RooWorkspace('qcdfit_ws')
    #simpdf, obs = qcdmodel.renderRoofit(qcdfit_ws)
    #qcdfit = simpdf.fitTo(obs,
    #                      ROOT.RooFit.Extended(True),
    #                      ROOT.RooFit.SumW2Error(True),
    #                      ROOT.RooFit.Strategy(2),
    #                      ROOT.RooFit.Save(),
    #                      ROOT.RooFit.Minimizer('Minuit2', 'migrad'),
    #                      ROOT.RooFit.PrintLevel(-1),
    #                      )
    #qcdfit_ws.add(qcdfit)
    #if "pytest" not in sys.modules:
    #     qcdfit_ws.writeToFile(os.path.join(str(carddir), 'HHModel_qcdfit.root'))
    #if qcdfit.status() != 0:
    #    raise RuntimeError('Could not fit qcd')

    #param_names = [p.name for p in tf_MCtempl.parameters.reshape(-1)]
    #decoVector = rl.DecorrelatedNuisanceVector.fromRooFitResult(tf_MCtempl.name + '_deco', qcdfit, param_names)
    #tf_MCtempl.parameters = decoVector.correlated_params.reshape(tf_MCtempl.parameters.shape)
    #tf_MCtempl_params_final = tf_MCtempl(msdscaled)
    
    #transfer factor
    tf_dataResidual = rl.BernsteinPoly("tf_dataResidual_"+passBinName, (nDataTF,), ['msd'], limits=(0, 10))
    #tf_dataResidual = rl.BernsteinPoly("tf_dataResidual", (nDataTF,), ['msd'], limits=(0, 10))
    tf_dataResidual_params = tf_dataResidual(msdscaled)
    #tf_params = qcdeff * tf_MCtempl_params_final * tf_dataResidual_params
    tf_params_pass = qcdeffpass * tf_dataResidual_params
    tf_params_sr = qcdeffsr * tf_dataResidual_params
    
    # build actual fit model now
    model = rl.Model("HHModel")
    for region in ['pass'+passBinName, 'fail','SR'+passBinName, 'SRfail']:
        ch = rl.Channel(region)
        model.addChannel(ch)

        isPass = region == 'pass'+passBinName
        isSR = region=='SR'+passBinName
        isSRfail = region=='SRfail'
        
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
        #for sName in ['TTJets_'+passBinName, 'H_'+passBinName, 'HH_'+passBinName, 'VH_'+passBinName, 'ttH_'+passBinName, 'others_'+passBinName]:
            # get templates
            templ = templates[sName]
            stype = rl.Sample.SIGNAL if sName == 'HH' else rl.Sample.BACKGROUND
            sample = rl.TemplateSample(ch.name + '_' + sName, stype, templ)
            
            # set nuisance values
            sample.setParamEffect(lumi, 1.027)

            # set mc stat uncs
            #sample.autoMCStats()
        
            #shape systematics
            valuesNominal =  templ[0]
            systs = ['JMS', 'JMR', 'BDTMassShape', 'ttJetsCorr', 'BDTShape', 'PNetShape']
            for syst in systs:
                valuesUp = get_hist(inputfile, 'histJet2Mass'+catn+'_%s_%sUp'%(sName, syst), obs=msd)[0]
                valuesDown = get_hist(inputfile, 'histJet2Mass'+catn+'_%s_%sDown'%(sName, syst), obs=msd)[0]
                effectUp = np.ones_like(valuesNominal)
                effectDown = np.ones_like(valuesNominal)
                for i in range(len(valuesNominal)):
                    if valuesNominal[i] >  0.:
                        effectUp[i]   = valuesUp[i]/valuesNominal[i]
                        effectDown[i]   = valuesDown[i]/valuesNominal[i]

                syst_param = rl.NuisanceParameter(syst, 'shape')
                sample.setParamEffect(syst_param, effectUp, effectDown)
              
            ch.addSample(sample)

        # make up a data_obs by summing the MC templates above
        #yields = sum(tpl[0] for tpl in templates.values())
        yields = templates['Data'][0]
        data_obs = (yields, msd.binning, msd.name)
        ch.setObservation(data_obs)        

    failCh = model['fail']
    passCh = model['pass'+passBinName]
    
    srfailCh = model['SRfail']
    srCh = model['SR'+passBinName]

    qcdparams = np.array([rl.IndependentParameter('qcdparam_msdbin%d'%i, 0) for i in range(msd.nbins)])

    #sideband fail
    initial_qcd = failCh.getObservation().astype(float)  # was integer, and numpy complained about subtracting float from it
    for sample in failCh:
        initial_qcd -= sample.getExpectation(nominal=True)
    if np.any(initial_qcd < 0.):
        raise ValueError("initial_qcd negative for some bins..", initial_qcd)
    sigmascale = 10  # to scale the deviation from initial
    scaledparams = initial_qcd * (1 + sigmascale/np.maximum(1., np.sqrt(initial_qcd)))**qcdparams

    #signal region fail
    initial_qcd_sr = srfailCh.getObservation().astype(float)  # was integer, and numpy complained about subtracting float from it
    for sample in srfailCh:
        initial_qcd_sr -= sample.getExpectation(nominal=True)
    if np.any(initial_qcd_sr < 0.):
        raise ValueError("initial_qcd_sr negative for some bins..", initial_qcd_sr)    
    scaledparams_sr = initial_qcd_sr * (1 + sigmascale/np.maximum(1., np.sqrt(initial_qcd_sr)))**qcdparams
    
    fail_qcd = rl.ParametericSample('fail_qcd', rl.Sample.BACKGROUND, msd, scaledparams)
    failCh.addSample(fail_qcd)
        
    #name: channel name _ proc name
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
    parser.add_argument('--carddir', default='cards', type=str, dest='carddir', help= 'output card directory')
    parser.add_argument('--nbins', default=17, type=int, dest='nbins', help= 'number of bins')
    parser.add_argument('--nMCTF', default=0, type=int, dest='nMCTF', help= 'order of polynomial for TF from MC')
    parser.add_argument('--nDataTF', default=2, type=int, dest='nDataTF', help= 'order of polynomial for TF from Data')
    
    args = parser.parse_args()
    if not os.path.exists(args.carddir):
        os.mkdir(args.carddir)
    #create_datacard(args.inputfile, args.carddir, args.nbins, args.nMCTF, args.nDataTF, "Bin4", "fail")

    #for fitbin in ["Bin1", "Bin2", "Bin3"]:
    for fitbin in ["Bin1", "Bin2", "Bin3", "Bin4"]:
    #for fitbin in ["FitCR", "Bin1", "Bin2", "Bin3", "Bin4"]:
        os.system("rm -rf cards_"+fitbin)
        os.system("mkdir cards_"+fitbin)
    #    create_datacard(args.inputfile, "cards_"+fitbin, args.nbins, args.nMCTF, args.nDataTF, fitbin, "fail"+fitbin)
    #create_datacard(args.inputfile, "cards_FitCR", args.nbins, args.nMCTF, args.nDataTF, "FitCR", "failFitCR")
    create_datacard(args.inputfile, "cards_Bin1", args.nbins, args.nMCTF, args.nDataTF, "Bin1", "fail")
    create_datacard(args.inputfile, "cards_Bin2", args.nbins, args.nMCTF, args.nDataTF, "Bin2", "fail")
    create_datacard(args.inputfile, "cards_Bin3", args.nbins, args.nMCTF, args.nDataTF, "Bin3", "fail")
    create_datacard(args.inputfile, "cards_Bin4", args.nbins, args.nMCTF, args.nDataTF, "Bin4", "fail")

    #os.system("rm -rf cards_SRBin1")
    #os.system("mkdir cards_SRBin1")
    #create_datacard(args.inputfile, "cards_SRBin1", args.nbins, args.nMCTF, args.nDataTF, "Bin1", "fail")
