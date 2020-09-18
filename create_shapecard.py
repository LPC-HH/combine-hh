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
from create_datacard import get_hist

def create_datacard(inputfile, carddir):

    lumi = rl.NuisanceParameter('CMS_lumi', 'lnN')

    msdbins = np.linspace(35, 215, 9+1)
    msd = rl.Observable('msd', msdbins)
    msdpts = msdbins[:-1] + 0.5 * np.diff(msdbins)
    msdscaled = (msdpts - 35.)/(215. - 35.)

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
        for sName in ['TTJets', 'ggH', 'HH', 'VH', 'ttH', 'QCD']:
            # get templates
            templ = templates[sName]
            stype = rl.Sample.SIGNAL if sName == 'HH' else rl.Sample.BACKGROUND
            sample = rl.TemplateSample(ch.name + '_' + sName, stype, templ)
            
            # set nuisance values
            sample.setParamEffect(lumi, 1.027)
            
            # set mc stat uncs
            sample.autoMCStats()

            ch.addSample(sample)

        # make up a data_obs by summing the MC templates above
        yields = sum(tpl[0] for tpl in templates.values())
        data_obs = (yields, msd.binning, msd.name)
        ch.setObservation(data_obs)        

    failCh = model['fail']
    passCh = model['pass']

    with open(os.path.join(str(carddir), 'HHModel.pkl'), "wb") as fout:
        pickle.dump(model, fout)

    model.renderCombine(os.path.join(str(carddir), 'HHModel'))


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--inputfile', default='HHTo4BPlots_Run2.root', type=str, dest='inputfile', help='input ROOT file')
    parser.add_argument('--carddir', default='cards_shapes', type=str, dest='carddir', help= 'output card directory')
    
    args = parser.parse_args()
    if not os.path.exists(args.carddir):
        os.mkdir(args.carddir)

    create_datacard(args.inputfile, args.carddir)
