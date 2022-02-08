from __future__ import print_function, division
from create_datacard import get_hist
import os
import rhalphalib as rl
import numpy as np
import pickle
import uproot
rl.util.install_roofit_helpers()
rl.ParametericSample.PreferRooParametricHist = False


def create_datacard_TTCR(inputfile, carddir, region):

    # open uproot file once
    upfile = uproot.open(inputfile)

    lumi = rl.NuisanceParameter('CMS_lumi', 'lnN')

    msdbins = np.linspace(50, 220, 17+1)
    msd = rl.Observable('msd', msdbins)
    msdpts = msdbins[:-1] + 0.5 * np.diff(msdbins)
    (msdpts - 50.)/(220. - 50.)

    # build actual fit model now
    model = rl.Model("HHModel")
    ch = rl.Channel(region)
    model.addChannel(ch)

    templates = {
        'TTJets': get_hist(upfile, 'histJet2Mass_%s_TTJets' % region, obs=msd),
        'others': get_hist(upfile, 'histJet2Mass_%s_others' % region, obs=msd),
        'QCD': get_hist(upfile, 'histJet2Mass_%s_QCD' % region, obs=msd),
        'Data': get_hist(upfile, 'histJet2Mass_%s_Data' % region, obs=msd),
    }
    for sName in ['TTJets', 'others', 'QCD']:
        # get templates
        templ = templates[sName]
        stype = rl.Sample.SIGNAL if sName == 'TTJets' else rl.Sample.BACKGROUND
        sample = rl.TemplateSample(ch.name + '_' + sName, stype, templ)

        # set nuisance values
        sample.setParamEffect(lumi, 1.016)

        # set mc stat uncs
        sample.autoMCStats()
        # shape systematics
        valuesNominal = templ[0]

        systs = {
            'pileupWeight': 'CMS_pileup',
            'JES': 'CMS_JES',
            'JMS': 'CMS_JMS',
            'JMR': 'CMS_JMR',
        }

        for syst in systs:
            valuesUp = get_hist(upfile, 'histJet2Mass_%s_%s_%sUp' % (region, sName, syst), obs=msd)[0]
            valuesDown = get_hist(upfile, 'histJet2Mass_%s_%s_%sDown' % (region, sName, syst), obs=msd)[0]
            effectUp = np.ones_like(upfile)
            effectDown = np.ones_like(valuesNominal)
            mask = (valuesNominal > 0)
            effectUp[mask] = valuesUp[mask]/valuesNominal[mask]
            effectDown[mask] = valuesDown[mask]/valuesNominal[mask]
            syst_param = rl.NuisanceParameter(systs[syst], 'shape')
            sample.setParamEffect(syst_param, effectUp, effectDown)

        ch.addSample(sample)

    # observed data
    yields = templates['Data'][0]
    data_obs = (yields, msd.binning, msd.name)
    ch.setObservation(data_obs)

    print("INFO: output path: ", carddir)
    with open(os.path.join(str(carddir), 'HHModel.pkl'), "wb") as fout:
        pickle.dump(model, fout)
        print("INFO: finish dump")

    model.renderCombine(os.path.join(str(carddir), 'HHModel'))
    print("INFO: after renderCombine")


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--inputfile', default='HHTo4BPlots_Run2_ttbarSkim_BDTv8p2.root', type=str, dest='inputfile', help='input ROOT file')
    parser.add_argument('--carddir', default='cards_shapes', type=str, dest='carddir', help='output card directory')

    args = parser.parse_args()
    if not os.path.exists(args.carddir+"_TTBarCR"):
        os.mkdir(args.carddir+"_TTBarCR")

    create_datacard_TTCR(args.inputfile, args.carddir+"_TTBarCR", "TTBarCR")
