from __future__ import print_function, division
import os
import rhalphalib as rl
from create_datacard import create_datacard
rl.util.install_roofit_helpers()
rl.ParametericSample.PreferRooParametricHist = False

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--inputfile', default='HHTo4BPlots_Run2_BDTv8p2_0311_syst_Trigv0.root', type=str, dest='inputfile', help='input ROOT file')
    parser.add_argument('--carddir', default='cards', type=str, dest='carddir', help='output card directory')
    parser.add_argument('--nbins', default=17, type=int, dest='nbins', help='number of bins')
    parser.add_argument('--include-ac', action='store_true', help='whether to include anomalous coupling processes for scans')

    args = parser.parse_args()
    if not os.path.exists(args.carddir):
        os.makedirs(args.carddir)

    binNames = ['Bin1', 'Bin2', 'Bin3']

    nDataTFDict = {}  # order of data TF polynomial
    nDataTFDict['Bin1'] = 0
    nDataTFDict['Bin2'] = 0
    nDataTFDict['Bin3'] = 0

    for fitbin in binNames:
        realdir = os.path.join(args.carddir, 'cards_'+fitbin)
        os.system('rm -rf %s' % realdir)
        os.makedirs(realdir)

        print('INFO: creating card for %s' % fitbin)
        create_datacard(args.inputfile, realdir, args.nbins, 0, nDataTFDict[fitbin], fitbin, "fail", add_unblinded=True, include_ac=args.include_ac)
