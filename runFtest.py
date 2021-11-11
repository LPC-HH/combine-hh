import ROOT as r
import os
from optparse import OptionParser


def exec_me(command, outf, dryRun=False):
    print command
    outf.write("%s\n" % command)
    if not dryRun:
        os.system(command)


def buildcats(ifile, odir, muonCR, suffix):
    # get N ptbins
    tf = r.TFile(ifile)
    ncats = tf.Get("data_obs_pass").GetYaxis().GetNbins()
    cats = []
    for icat in range(1, ncats+1):
        cats.append({"name": "cat%s" % icat, "card": odir+"card_rhalphabet_cat%s.txt" % icat})
    if muonCR:
        cats.append({"name": "muonCR", "card": odir+"datacard_muonCR.txt"})
    if suffix:
        for catdict in cats:
            catdict['name'] = catdict['name']+"_"+suffix
    return cats


def buildcards(odir, v1n, v2n, options):
    ifile = options.ifile
    dryRun = options.dryRun

    ifile.split("/")[-1]
    if odir == "":
        odir = os.path.dirname(ifile)
        print "using default output dir:", odir
    create_cards = "python create_datacard.py --inputfile=%s --carddir=%s --nbins=%i --nDataTF=%i --passBinName=%s --blinded %s" % (ifile, odir, options.n, v1n, options.passBinName, options.blinded)
    if options.testMCTF:
        create_cards = "python create_datacard.py --inputfile=%s --carddir=%s --nbins=%i --nMCTF=%i --passBinName=%s --blinded %s" % (
            ifile, odir, options.n, v1n, options.passBinName, options.blinded)

    if int(options.blinded):
        combineCards = "cd %s/HHModel; combineCards.py pass=pass%s.txt fail=fail.txt > HHModel_combined.txt; text2workspace.py HHModel_combined.txt ;cd -" % (odir, options.passBinName)
    else:
        combineCards = "cd %s/HHModel; combineCards.py pass=SR%s.txt fail=fitfail.txt > HHModel_combined.txt; text2workspace.py HHModel_combined.txt ;cd -" % (odir, options.passBinName)
    wsRoot = "%s/HHModel_combined_n%i.root" % (odir, v1n)
    cpCards = "cp %s/HHModel/HHModel_combined.root %s" % (odir, wsRoot)

    cmds = [
        create_cards,
        combineCards,
        cpCards
    ]
    if options.justPlot:
        return wsRoot
    for cmd in cmds:
        exec_me(cmd, logf, dryRun)
    # return name of root file product
    return wsRoot


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('-m', '--mass', action='store', type='int', dest='mass', default=125, help='mass')
    parser.add_option('--v1n1', '--V1N1', action='store', type='int', dest='V1N1', default=1, help='order of variable 1 polynomial for model 1')
    parser.add_option('--v2n1', '--V2N1', action='store', type='int', dest='V2N1', default=-1, help='order of variable 2 polynomial for model 1, can be ignored if 1D')
    parser.add_option('--v1n2', '--V1N2', action='store', type='int', dest='V1N2', default=2, help='order of variable 1 polynomial for model 2')
    parser.add_option('--v2n2', '--V2N2', action='store', type='int', dest='V2N2', default=-1, help='order of variable 2 polynomial for model 2, can be ignored if 1D')
    parser.add_option('--scale', dest='scale', default=1, type='float', help='scale factor to scale MC (assuming only using a fraction of the data)')
    parser.add_option('-l', '--lumi', action='store', type='float', dest='lumi', default=137.0, help='lumi')
    parser.add_option('-i', '--ifile', dest='ifile', default='HHTo4BPlots_Run2_BDTv8p2.root', help='file with histogram inputs', metavar='ifile')
    parser.add_option('--ifile-loose', dest='ifile_loose', default=None, help='second file with histogram inputs (looser b-tag cut to take W/Z/H templates)',
                      metavar='ifile_loose')
    parser.add_option('--suffix', dest='suffix', default=None, help='suffix for conflict variables', metavar='suffix')
    parser.add_option('--ifile-muon', dest='ifile_muon', default=None, help='path to muonCR templates ', metavar='ifile_muon')
    parser.add_option('-t', '--toys', action='store', type='int', dest='toys', default=200, help='number of toys')
    parser.add_option('-s', '--seed', action='store', type='int', dest='seed', default=1, help='random seed')
    parser.add_option('-r', '--r', dest='r', default=1, type='float', help='default value of r')
    parser.add_option('-n', '--n', action='store', type='int', dest='n', default=16, help='number of bins')
    parser.add_option('--just-plot', action='store_true', dest='justPlot', default=False, help='just plot')
    parser.add_option('--test-mc-tf', action='store_true', dest='testMCTF', default=False, help='do FTest on MC TF (default is on data TF)')
    parser.add_option('--pseudo', action='store_true', dest='pseudo', default=False, help='run on asimov dataset')
    parser.add_option('-y', '--year', type='choice', dest='year', default='2016', choices=['2016', '2017', '2018', 'all'], help='switch to use different year ', metavar='year')
    parser.add_option('--blind', action='store_true', dest='blind', default=False, help='run on blinded dataset', metavar='blind')
    parser.add_option('--MiNLO', action='store_true', dest='MiNLO', default=False, help='MiNLO unc.', metavar='MiNLO')
    parser.add_option('--qcdTF', action='store_true', dest='qcdTF', default=False, help='switch to make qcdTF cards', metavar='qcdTF')
    parser.add_option('--exp', action='store_true', dest='exp', default=False, help='use exp(bernstein poly) transfer function', metavar='exp')
    parser.add_option('--freezeNuisances', action='store', type='string', dest='freezeNuisances', default='None', help='freeze nuisances')
    parser.add_option('--setParameters', action='store', type='string', dest='setParameters', default='None', help='setParameters')
    parser.add_option('--dry-run', dest="dryRun", default=False, action='store_true',
                      help="Just print out commands to run")
    parser.add_option('-o', '--odir', dest='odir', default='FTest', help='directory to write plots', metavar='odir')
    parser.add_option('--passBinName', default='Bin1', choices=['Bin1', 'Bin2', 'Bin3'], dest='passBinName', help='pass bin name')
    parser.add_option('--blinded', default=False, dest='blinded', help='run with data on SR')
    (options, args) = parser.parse_args()

    logf = open(options.ifile.replace(".root", "_report.txt"), "w")
    logf.write("=======runFtest.py==========\n")
    logf.write("===ifile = %s ==========\n" % options.ifile)
    logf.write("===odir  = %s ==========\n" % options.odir)
    print "=======runFtest.py=========="
    print "===ifile = %s ==========" % options.ifile
    print "===odir  = %s ==========" % options.odir

    card_dir_base = '%s/cards' % (options.odir)
    if options.pseudo:
        card_dir_base = '%s/cards_mc' % (options.odir)
    if options.V2N1 >= 0 and options.V2N2 >= 0:  # if 2D
        cardsDir1 = '%s_v1n1i%i_v2n1i%i' % (card_dir_base, options.V1N1, options.V2N1)
        cardsDir2 = '%s_v1n2i%i_v2n2i%i' % (card_dir_base, options.V1N2, options.V2N2)
        toysDir = "%s/toys_v1n1i%i_v1n2i%i_v2n1i%i_v2n2i%i" % (options.odir, options.V1N1, options.V1N2, options.V2N1, options.V2N2)
    else:  # if 1D
        cardsDir1 = '%s_n1i%i' % (card_dir_base, options.V1N1)
        cardsDir2 = '%s_n2i%i' % (card_dir_base, options.V1N2)
        toysDir = "%s/toys_n1i%i_n2i%i" % (options.odir, options.V1N1, options.V1N2)

    if not options.justPlot:
        exec_me('mkdir -p %s' % options.odir, logf, options.dryRun)
        exec_me('mkdir -p %s' % (toysDir), logf, options.dryRun)
        exec_me('mkdir -p %s' % cardsDir1, logf, options.dryRun)
        exec_me('mkdir -p %s' % cardsDir2, logf, options.dryRun)
        datacardWS1 = buildcards(cardsDir1, options.V1N1, options.V2N1, options)
        datacardWS2 = buildcards(cardsDir2, options.V1N2, options.V2N2, options)
    else:
        datacardWS1 = buildcards(cardsDir1, options.V1N1, options.V2N1, options)
        datacardWS2 = buildcards(cardsDir2, options.V1N2, options.V2N2, options)

    p1 = options.V1N1+1+1
    p2 = options.V1N2+1+1
    if options.V2N1 >= 0 and options.V2N2 >= 0:
        p1 = int((options.V1N1+1)*(options.V2N1+1)) + 1  # paramaters including floating signals
        p2 = int((options.V1N2+1)*(options.V2N2+1)) + 1  # parameters including floating signals

    if 'r' in options.freezeNuisances.split(","):
        p1 = p1-1
        p2 = p2-1

    dataString = ''
    if not options.pseudo:
        dataString = '--data'

    if not options.justPlot:
        if options.blinded:
            limit_cmd = 'python limit.py -M FTest --datacard %s ' + \
                        '--datacard-alt %s -o %s -n %i --p1 %i --p2 %i ' + \
                        '-t %i --lumi %f %s -r %f --seed %s --freezeNuisances %s ' + \
                        '--setParameters %s --V1N1 %s --V2N1 %s --V1N2 %s --V2N2 %s --blinded %s'
            limit_cmd = limit_cmd % (datacardWS1,
                                     datacardWS2,
                                     toysDir,
                                     options.n,
                                     p1,
                                     p2,
                                     options.toys,
                                     options.lumi,
                                     dataString,
                                     options.r,
                                     options.seed,
                                     options.freezeNuisances,
                                     options.setParameters,
                                     options.V1N1,
                                     options.V2N1,
                                     options.V1N2,
                                     options.V2N2,
                                     options.blinded)
            exec_me(limit_cmd, logf, options.dryRun)
        else:
            limit_cmd = 'python limit.py -M FTest --datacard %s ' + \
                        '--datacard-alt %s -o %s -n %i --p1 %i --p2 %i ' + \
                        '--lumi %f %s ' + \
                        '--V1N1 %s --V2N1 %s --V1N2 %s --V2N2 %s --blinded %s'
            limit_cmd = limit_cmd % (datacardWS1,
                                     datacardWS2,
                                     toysDir,
                                     options.n,
                                     p1,
                                     p2,
                                     options.lumi,
                                     dataString,
                                     options.V1N1,
                                     options.V2N1,
                                     options.V1N2,
                                     options.V2N2,
                                     options.blinded)
            exec_me(limit_cmd, logf, options.dryRun)
    else:
        # use toys from hadd-ed directory
        toysDir += "/toys/"
        if options.blinded:
            limit_cmd = 'python limit.py -M FTest --datacard %s ' + \
                        '--datacard-alt %s -o %s -n %i --p1 %i --p2 %i -t %i ' + \
                        '--lumi %f %s -r %f --seed %s --freezeNuisances %s ' + \
                        '--setParameters %s --V1N1 %s --V2N1 %s --V1N2 %s --V2N2 %s--blinded %s'
            limit_cmd = limit_cmd % (datacardWS1,
                                     datacardWS2,
                                     toysDir,
                                     options.n,
                                     p1,
                                     p2,
                                     options.toys,
                                     options.lumi,
                                     dataString,
                                     options.r,
                                     options.seed,
                                     options.freezeNuisances,
                                     options.setParameters,
                                     options.V1N1,
                                     options.V2N1,
                                     options.V1N2,
                                     options.V2N2,
                                     options.blinded)
            exec_me(limit_cmd+" --just-plot ", logf, options.dryRun)
        else:
            limit_cmd = 'python limit.py -M FTest --datacard %s ' + \
                        '--datacard-alt %s -o %s -n %i --p1 %i --p2 %i ' + \
                        '--lumi %f %s ' + \
                        '--V1N1 %s --V2N1 %s --V1N2 %s --V2N2 %s --blinded %s'
            limit_cmd = limit_cmd % (datacardWS1,
                                     datacardWS2,
                                     toysDir,
                                     options.n,
                                     p1,
                                     p2,
                                     options.lumi,
                                     dataString,
                                     options.V1N1,
                                     options.V2N1,
                                     options.V1N2,
                                     options.V2N2,
                                     options.blinded)
            exec_me(limit_cmd, logf, options.dryRun)
