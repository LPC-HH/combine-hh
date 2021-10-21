from __future__ import print_function, division
from create_datacard import get_hist
import os
import rhalphalib as rl
import numpy as np
import pickle
rl.util.install_roofit_helpers()
rl.ParametericSample.PreferRooParametricHist = False


def create_datacard(inputfile, carddir, passBinName, failBinName):

    lumi = rl.NuisanceParameter('CMS_lumi', 'lnN')

    msdbins = np.linspace(50, 220, 17+1)
    msd = rl.Observable('msd', msdbins)
    msdpts = msdbins[:-1] + 0.5 * np.diff(msdbins)
    (msdpts - 50.)/(220. - 50.)

    # build actual fit model now
    model = rl.Model("HHModel")
    for region in ['TTBarCR']:
        ch = rl.Channel(region)
        model.addChannel(ch)

        isPass = region == 'TTBarCR'
        templates = {
            'TTJets': get_hist(inputfile, 'histJet2Mass%s_TTJets' % ('_'+passBinName if isPass else '_'+failBinName), obs=msd),
            'others': get_hist(inputfile, 'histJet2Mass%s_others' % ('_'+passBinName if isPass else '_'+failBinName), obs=msd),
            'QCD': get_hist(inputfile, 'histJet2Mass%s_QCD' % ('_'+passBinName if isPass else '_'+failBinName), obs=msd),
            'Data': get_hist(inputfile, 'histJet2Mass%s_Data' % ('_'+passBinName if isPass else '_'+failBinName), obs=msd),
        }
        for sName in ['TTJets', 'others', 'QCD']:
            # get templates
            templ = templates[sName]
            stype = rl.Sample.SIGNAL if sName == 'TTJets' else rl.Sample.BACKGROUND
            sample = rl.TemplateSample(ch.name + '_' + sName, stype, templ)

            # set nuisance values
            sample.setParamEffect(lumi, 1.018)

            # set mc stat uncs
            sample.autoMCStats()
            # shape systematics
            valuesNominal = templ[0]
            #systs = ['JMS', 'JMR', 'ttJetsCorr', 'BDTShape', 'pileupWeight', 'JES', 'PNetShape']
            systs = ['JMS', 'JMR', 'pileupWeight', 'JES']
            for syst in systs:
                valuesUp = get_hist(inputfile, 'histJet2Mass%s_%s_%sUp' % ('_'+passBinName if isPass else '_'+failBinName, sName, syst), obs=msd)[0]
                valuesDown = get_hist(inputfile, 'histJet2Mass%s_%s_%sDown' % ('_'+passBinName if isPass else '_'+failBinName, sName, syst), obs=msd)[0]
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
        #yields = sum(tpl[0] for tpl in templates.values())
        yields = templates['Data'][0]
        data_obs = (yields, msd.binning, msd.name)
        ch.setObservation(data_obs)

    model['TTBarCR']

    print("output path: ", carddir)
    with open(os.path.join(str(carddir), 'HHModel.pkl'), "wb") as fout:
        pickle.dump(model, fout)
        print("finish dump")

    model.renderCombine(os.path.join(str(carddir), 'HHModel'))
    print("after renderCombine")


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--inputfile', default='HHTo4BPlots_Run2_ttbarSkim_BDTv8p2.root', type=str, dest='inputfile', help='input ROOT file')
    parser.add_argument('--carddir', default='cards_shapes', type=str, dest='carddir', help='output card directory')

    args = parser.parse_args()
    if not os.path.exists(args.carddir+"_TTBarCR"):
        os.mkdir(args.carddir+"_TTBarCR")

    create_datacard(args.inputfile, args.carddir+"_TTBarCR", "TTBarCR", "fail")
