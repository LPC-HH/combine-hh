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
    hist_values = upfile[name].values
    hist_edges = upfile[name].edges
    if obs.binning != hist_edges:
        # rebin (assumes new bins are a subset of existing bins)
        edge_mask = np.in1d(hist_edges,obs.binning)
        hist_mask = np.logical_and(edge_mask[0:-1], edge_mask[1:])
        hist_values = hist_values[hist_mask]
        hist_edges = hist_edges[edge_mask]
    return (hist_values, hist_edges, obs.name)

def create_datacard(inputfile, carddir):

    lumi = rl.NuisanceParameter('CMS_lumi', 'lnN')

    msdbins = np.linspace(35, 215, 9+1)
    msd = rl.Observable('msd', msdbins)
    msdpts = msdbins[:-1] + 0.5 * np.diff(msdbins)
    msdscaled = (msdpts - 35.)/(215. - 35.)

    # Build qcd MC pass+fail model and fit to polynomial
    qcdmodel = rl.Model('qcdmodel')
    qcdpass, qcdfail = 0., 0.
    failCh = rl.Channel('fail')
    passCh = rl.Channel('pass')
    qcdmodel.addChannel(failCh)
    qcdmodel.addChannel(passCh)
    # pseudodata MC template
    failTempl = get_hist(inputfile, 'histJet2Mass_fail_QCD', obs=msd)
    passTempl = get_hist(inputfile, 'histJet2Mass_QCD', obs=msd)
    failCh.setObservation(failTempl)
    passCh.setObservation(passTempl)
    qcdfail = failCh.getObservation().sum()
    qcdpass = passCh.getObservation().sum()

    qcdeff = qcdpass / qcdfail
    tf_MCtempl = rl.BernsteinPoly("tf_MCtempl", (2,), ['msd'], limits=(0, 10))
    tf_MCtempl_params = qcdeff * tf_MCtempl(msdscaled)
    
    failCh = qcdmodel['fail']
    passCh = qcdmodel['pass']
    failObs = failCh.getObservation()
    qcdparams = np.array([rl.IndependentParameter('qcdparam_msdbin%d'%i, 0) for i in range(msd.nbins)])
    sigmascale = 10.
    scaledparams = failObs * (1 + sigmascale/np.maximum(1., np.sqrt(failObs)))**qcdparams
    fail_qcd = rl.ParametericSample('fail_qcd', rl.Sample.BACKGROUND, msd, scaledparams)
    failCh.addSample(fail_qcd)
    pass_qcd = rl.TransferFactorSample('pass_qcd', rl.Sample.BACKGROUND, tf_MCtempl_params, fail_qcd)
    passCh.addSample(pass_qcd)
    
    qcdfit_ws = ROOT.RooWorkspace('qcdfit_ws')
    simpdf, obs = qcdmodel.renderRoofit(qcdfit_ws)
    qcdfit = simpdf.fitTo(obs,
                          ROOT.RooFit.Extended(True),
                          ROOT.RooFit.SumW2Error(True),
                          ROOT.RooFit.Strategy(2),
                          ROOT.RooFit.Save(),
                          ROOT.RooFit.Minimizer('Minuit2', 'migrad'),
                          ROOT.RooFit.PrintLevel(-1),
                          )
    qcdfit_ws.add(qcdfit)
    if "pytest" not in sys.modules:
         qcdfit_ws.writeToFile(os.path.join(str(carddir), 'HHModel_qcdfit.root'))
    if qcdfit.status() != 0:
        raise RuntimeError('Could not fit qcd')

    param_names = [p.name for p in tf_MCtempl.parameters.reshape(-1)]
    decoVector = rl.DecorrelatedNuisanceVector.fromRooFitResult(tf_MCtempl.name + '_deco', qcdfit, param_names)
    tf_MCtempl.parameters = decoVector.correlated_params.reshape(tf_MCtempl.parameters.shape)
    tf_MCtempl_params_final = tf_MCtempl(msdscaled)
    tf_dataResidual = rl.BernsteinPoly("tf_dataResidual", (2,), ['msd'], limits=(0, 10))
    tf_dataResidual_params = tf_dataResidual(msdscaled)
    tf_params = qcdeff * tf_MCtempl_params_final * tf_dataResidual_params

    # build actual fit model now
    model = rl.Model("HHModel")
    for region in ['pass', 'fail']:
        ch = rl.Channel(region)
        model.addChannel(ch)

        isPass = region == 'pass'
        templates = {
            'TTJets': get_hist(inputfile, 'histJet2Mass%s_TTJets'%('' if isPass else '_fail'), obs=msd),
            'ggH': get_hist(inputfile, 'histJet2Mass%s_H'%('' if isPass else '_fail'), obs=msd),
            'HH': get_hist(inputfile, 'histJet2Mass%s_HH'%('' if isPass else '_fail'), obs=msd),
            'VH': get_hist(inputfile, 'histJet2Mass%s_VH'%('' if isPass else '_fail'), obs=msd),
            'ttH': get_hist(inputfile, 'histJet2Mass%s_ttH'%('' if isPass else '_fail'), obs=msd),
            'QCD': get_hist(inputfile, 'histJet2Mass%s_QCD'%('' if isPass else '_fail'), obs=msd),
        }
        for sName in ['TTJets', 'ggH', 'HH', 'VH', 'ttH']:
            # get templates
            templ = templates[sName]
            stype = rl.Sample.SIGNAL if sName == 'HH' else rl.Sample.BACKGROUND
            sample = rl.TemplateSample(ch.name + '_' + sName, stype, templ)
            
            # set nuisance valies
            sample.setParamEffect(lumi, 1.027)

            ch.addSample(sample)

        # make up a data_obs by summing the MC templates above
        yields = sum(tpl[0] for tpl in templates.values())
        data_obs = (yields, msd.binning, msd.name)
        ch.setObservation(data_obs)        

    failCh = model['fail']
    passCh = model['pass']

    qcdparams = np.array([rl.IndependentParameter('qcdparam_msdbin%d'%i, 0) for i in range(msd.nbins)])
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
    parser.add_argument('--inputfile', default='HHTo4BPlots_Run2.root', type=str, dest='inputfile', help='input ROOT file')
    parser.add_argument('--carddir', default='cards', type=str, dest='carddir', help= 'output card directory')
    
    args = parser.parse_args()
    if not os.path.exists(args.carddir):
        os.mkdir(args.carddir)

    create_datacard(args.inputfile, args.carddir)
