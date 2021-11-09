#!/usr/bin/env python
from __future__ import print_function, division
import ROOT as r
import sys
import os
from optparse import OptionParser

import subprocess


def exec_me(command, dryRun=False):
    print(command)
    if not dryRun:
        os.system(command)


def end():
    if __name__ == '__main__':
        try:
            input = raw_input
        except NameError:
            pass
        rep = ''
        while rep not in ['q', 'Q', 'a', ' ']:
            rep = input('enter "q" to quit: ')
            if 1 < len(rep):
                rep = rep[0]


def plotgaus(iFName, injet, iLabel, options):
    lCan = r.TCanvas(str(iLabel), str(iLabel), 500, 400)
    lCan.SetLeftMargin(0.12)
    lCan.SetBottomMargin(0.15)
    lCan.SetTopMargin(0.12)
    if isinstance(iFName, str):
        lFile = r.TFile(iFName)
        lTree = lFile.Get("tree_fit_sb")
    elif isinstance(iFName, []):
        lTree = r.TChain("tree_fit_sb")
        for f in iFName:
            lTree.Add(f)

    lH = r.TH1D('h_bias', 'h_bias', 50, -4, 4)
    lH_1 = r.TH1D('h_bias_1', 'h_bias', 50, -4, 4)
    lH_2 = r.TH1D('h_bias_2', 'h_bias', 50, -4, 4)
    lTree.Project('h_bias_1', '(%s-%s)/%sLoErr' % (options.poi, injet, options.poi),
                  '%s>%s&&(%sHiErr+%s)<%i&&(%s-%sLoErr)>%i' % (options.poi, injet,
                                                               options.poi, options.poi, float(options.rMax)-1,
                                                               options.poi, options.poi, float(options.rMin)+1))
    lTree.Project('h_bias_2', '(%s-%s)/%sHiErr' % (options.poi, injet, options.poi),
                  '%s<%s&&(%sHiErr+%s)<%i&&(%s-%sLoErr)>%i' % (options.poi, injet,
                                                               options.poi, options.poi, float(options.rMax)-1,
                                                               options.poi, options.poi, float(options.rMin)+1))
    lH = lH_1
    lH.Add(lH_2)
    print('Tree Entries = %s , pull entries = %s' % (lTree.GetEntriesFast(), lH.GetEntries()))
    print(lH.GetMean())
    print(lH.GetBinCenter(lH.GetMaximumBin()))
    gaus_func = r.TF1("gaus_func", "gaus(0)", -3, 3)
    gaus_func.SetParameter(0, 20)
    gaus_func.SetParameter(1, 0)
    gaus_func.SetParameter(2, 1)
    lH.Fit(gaus_func, "mler")
    gaus_func.Draw("same")
    muLabel = {'r': '#mu', 'r_z': '#mu_{Z}'}
    lH.GetXaxis().SetTitle("Bias (#hat{%s} - %s)/#sigma_{%s}" % (muLabel[options.poi], muLabel[options.poi], muLabel[options.poi]))
    lH.GetYaxis().SetTitle("Pseudoexperiments")
    lH.GetYaxis().SetTitleOffset(0.8)
    gaus_func.SetLineColor(r.kRed)
    gaus_func.SetLineStyle(2)
    lH.SetMaximum(2.*lH.GetMaximum())
    lH.Draw("ep")
    gaus_func.Draw("sames")
    lH.Draw("ep sames")

    tLeg = r.TLegend(0.5, 0.6, 0.89, 0.89)
    tLeg.SetLineColor(r.kWhite)
    tLeg.SetLineWidth(0)
    tLeg.SetFillStyle(0)
    tLeg.SetTextFont(42)
    if options.poi == 'r':
        tLeg.AddEntry(lH, "#splitline{Pseudodata}{Hbb(%s GeV) #mu=%s}" % (options.mass, options.r), "lep")
    elif options.poi == 'r_z':
        tLeg.AddEntry(lH, "#splitline{Pseudodata}{Zbb(%s GeV) #mu_{Z}=%s}" % ('90', options.r), "lep")
    tLeg.AddEntry(gaus_func, "#splitline{Gaussian fit}{mean = %+1.2f, s.d. = %1.2f}" % (gaus_func.GetParameter(1), gaus_func.GetParameter(2)), "l")
    tLeg.Draw("same")

    lat = r.TLatex()
    lat.SetTextAlign(11)
    lat.SetTextSize(0.06)
    lat.SetTextFont(62)
    lat.SetNDC()
    lat.DrawLatex(0.12, 0.91, "CMS")
    lat.SetTextSize(0.05)
    lat.SetTextFont(52)
    lat.DrawLatex(0.23, 0.91, "Preliminary")
    lat.SetTextFont(42)
    lat.DrawLatex(0.70, 0.91, "%.1f fb^{-1} (13 TeV)" % options.lumi)
    lat.SetTextFont(52)
    lat.SetTextSize(0.045)

    lat.DrawLatex(0.15, 0.82, 'gen. pdf = %s(n_{#rho}=%i,n_{p_{T}}=%i)' % (options.pdf2, options.V1N2, options.V2N2))
    lat.DrawLatex(0.15, 0.75, 'fit pdf = %s(n_{#rho}=%i,n_{p_{T}}=%i)' % (options.pdf1, options.V1N1, options.V2N1))

    lCan.Modified()
    lCan.Update()
    lCan.SaveAs(options.odir+'/'+iLabel+".pdf")
    lCan.SaveAs(options.odir+'/'+iLabel+".png")
    lCan.SaveAs(options.odir+'/'+iLabel+".C")


def plotftest(iToys, iCentral, prob, iLabel, options):
    lCan = r.TCanvas(str(iLabel), str(iLabel), 800, 600)
    lCan.SetLeftMargin(0.12)
    lCan.SetBottomMargin(0.12)
    lCan.SetRightMargin(0.1)
    lCan.SetTopMargin(0.1)

    if options.method == 'FTest':
        lH = r.TH1F(iLabel+"hist", iLabel+"hist", 100, 0, min(max(max(iToys), iCentral)*1.1, 10.0))
        lH_cut = r.TH1F(iLabel+"hist", iLabel+"hist", 100, 0, min(max(max(iToys), iCentral)*1.1, 10.0))
    elif options.method == 'GoodnessOfFit' and options.algo == 'saturated':
        lH = r.TH1F(iLabel+"hist", iLabel+"hist", 100, 0, max(max(iToys), iCentral)*1.1)
        lH_cut = r.TH1F(iLabel+"hist", iLabel+"hist", 100, 0, max(max(iToys), iCentral)*1.1)
    elif options.method == 'GoodnessOfFit' and options.algo == 'KS':
        lH = r.TH1F(iLabel+"hist", iLabel+"hist", 70, 0, max(max(iToys), iCentral)+0.05)
        lH_cut = r.TH1F(iLabel+"hist", iLabel+"hist", 70, 0, max(max(iToys), iCentral)+0.05)

    if options.method == 'FTest':
        lH.GetXaxis().SetTitle("F = #frac{-2log(#lambda_{1}/#lambda_{2})/(p_{2}-p_{1})}{-2log#lambda_{2}/(n-p_{2})}")
        lH.GetXaxis().SetTitleSize(0.025)
        lH.GetXaxis().SetTitleOffset(2)
        lH.GetYaxis().SetTitle("Pseudodatasets")
        lH.GetYaxis().SetTitleOffset(0.85)
    elif options.method == 'GoodnessOfFit' and options.algo == 'saturated':
        lH.GetXaxis().SetTitle("-2log#lambda")
        lH.GetYaxis().SetTitle("Pseudodatasets")
        lH.GetYaxis().SetTitleOffset(0.85)
    elif options.method == 'GoodnessOfFit' and options.algo == 'KS':
        lH.GetXaxis().SetTitle("KS")
        lH.GetYaxis().SetTitle("Pseudodatasets")
        lH.GetYaxis().SetTitleOffset(0.85)
    for val in iToys:
        lH.Fill(val)
        if val > iCentral:
            lH_cut.Fill(val)
    lH.SetMarkerStyle(20)
    lH.Draw("pez")
    lLine = r.TArrow(iCentral, 0.25*lH.GetMaximum(), iCentral, 0)
    lLine.SetLineColor(r.kBlue+1)
    lLine.SetLineWidth(2)

    lH_cut.SetLineColor(r.kViolet-10)
    lH_cut.SetFillColor(r.kViolet-10)
    lH_cut.Draw("histsame")

    if options.method == 'FTest':
        fdist = r.TF1("fDist", "[0]*TMath::FDist(x, [1], [2])", 0, min(max(max(iToys), iCentral)*1.1, 10.0))
        fdist.SetParameter(0, lH.Integral()*((min(max(max(iToys), iCentral)*1.0, 10.0))/70.))
        fdist.SetParameter(1, options.p2-options.p1)
        fdist.SetParameter(2, options.n-options.p2)
        fdist.Draw('same')
    elif options.method == 'GoodnessOfFit' and options.algo == 'saturated':
        chi2_func = r.TF1('chisqpdf', '[0]*ROOT::Math::chisquared_pdf(x,[1])', 0, max(max(iToys), iCentral)*1.1)
        chi2_func.SetParameter(0, lH.Integral())
        chi2_func.SetParameter(1, 50)
        chi2_func.Draw('same')
        lH.Fit(chi2_func, "mle")
    lH.Draw("pezsame")
    lLine.Draw()

    tLeg = r.TLegend(0.5, 0.5, 0.88, 0.88)
    tLeg.SetLineColor(r.kWhite)
    tLeg.SetLineWidth(0)
    tLeg.SetFillStyle(0)
    tLeg.SetTextFont(42)
    tLeg.AddEntry(lH, "toy data (N_{toys}=%i)" % len(iToys), "lep")
    tLeg.AddEntry(lLine, "observed = %.3f" % iCentral, "l")
    tLeg.AddEntry(lH_cut, "p-value = %.2f" % (1-prob), "f")
    if options.method == 'FTest':
        tLeg.AddEntry(fdist, "F-dist, ndf = (%.0f, %.0f) " % (fdist.GetParameter(1), fdist.GetParameter(2)), "l")
    elif options.method == 'GoodnessOfFit' and options.algo == 'saturated':
        tLeg.AddEntry(chi2_func, "#chi^{2} fit, ndf = %.1f #pm %.1f" % (chi2_func.GetParameter(1), chi2_func.GetParError(1)), "l")

    tLeg.Draw("same")

    lat = r.TLatex()
    lat.SetTextAlign(11)
    lat.SetTextSize(0.06)
    lat.SetTextFont(62)
    lat.SetNDC()
    lat.DrawLatex(0.12, 0.91, "CMS")
    lat.SetTextSize(0.05)
    lat.SetTextFont(52)
    if options.isData:
        lat.DrawLatex(0.23, 0.91, "Preliminary")
    else:
        lat.DrawLatex(0.23, 0.91, "Simulation")
    lat.SetTextFont(42)
    lat.DrawLatex(0.65, 0.91, "%.0f fb^{-1} (13 TeV)" % options.lumi)
    lat.SetTextFont(52)
    lat.SetTextSize(0.045)

    lCan.SaveAs(options.odir+'/'+iLabel+".pdf")
    lCan.SaveAs(options.odir+'/'+iLabel+".png")
    lCan.SaveAs(options.odir+'/'+iLabel+".C")


def nllDiff(iFName1, iFName2):
    lFile1 = r.TFile.Open(iFName1)
    lTree1 = lFile1.Get("limit")
    lFile2 = r.TFile.Open(iFName2)
    lTree2 = lFile2.Get("limit")
    lDiffs = []
    for i0 in range(0, lTree1.GetEntries()):
        lTree1.GetEntry(i0)
        lTree2.GetEntry(i0)
        diff = 2*(lTree1.nll-lTree1.nll0)-2*(lTree2.nll-lTree2.nll0)
        lDiffs.append(diff)
    return lDiffs


def fStat(iFName1, iFName2, p1, p2, n):
    lFile1 = r.TFile.Open(iFName1)
    lTree1 = lFile1.Get("limit")
    lFile2 = r.TFile.Open(iFName2)
    lTree2 = lFile2.Get("limit")
    lDiffs = []
    for i0 in range(0, lTree1.GetEntries()):
        lTree1.GetEntry(i0)
        lTree2.GetEntry(i0)
        if lTree1.limit-lTree2.limit > 0:
            F = (lTree1.limit-lTree2.limit)/(p2-p1)/(lTree2.limit/(n-p2))
            print(i0, ":", lTree1.limit, "-", lTree2.limit, "=", lTree1.limit-lTree2.limit, "F =", F)
            lDiffs.append(F)
        else:
            lDiffs.append(0.0)
    print("number of toys with F>0: %s / %s" % (len(lDiffs), lTree1.GetEntries()))
    return lDiffs


def goodnessVals(iFName1):
    lFile1 = r.TFile.Open(iFName1)
    lTree1 = lFile1.Get("limit")
    lDiffs = []
    for i0 in range(0, lTree1.GetEntries()):
        lTree1.GetEntry(i0)
        lDiffs.append(lTree1.limit)
    return lDiffs


def ftest(base, alt, ntoys, iLabel, options):
    if not options.justPlot:
        baseName = base.split('/')[-1].replace('.root', '')
        altName = alt.split('/')[-1].replace('.root', '')

        if not int(options.blinded):
            exec_me('combine -M GoodnessOfFit %s --algorithm saturated -n %s' % (base, baseName), options.dryRun)
            exec_me('cp higgsCombine%s.GoodnessOfFit.mH120.root %s/base1.root' % (baseName, options.odir), options.dryRun)
            exec_me('combine -M GoodnessOfFit %s --algorithm saturated  -n %s' % (alt, altName), options.dryRun)
            exec_me('cp higgsCombine%s.GoodnessOfFit.mH120.root %s/base2.root' % (altName, options.odir), options.dryRun)

        else:
            exec_me('combine -M GoodnessOfFit %s  --rMax %s --rMin %s --algorithm saturated -n %s --freezeParameters %s --setParameters %s'
                    % (base, options.rMax, options.rMin, baseName, options.freezeNuisances, options.setParameters), options.dryRun)
            exec_me('cp higgsCombine%s.GoodnessOfFit.mH120.root %s/base1.root' % (baseName, options.odir), options.dryRun)
            exec_me('combine -M GoodnessOfFit %s --rMax %s --rMin %s --algorithm saturated  -n %s --freezeParameters %s --setParameters %s'
                    % (alt, options.rMax, options.rMin, altName, options.freezeNuisances, options.setParameters), options.dryRun)
            exec_me('cp higgsCombine%s.GoodnessOfFit.mH120.root %s/base2.root' % (altName, options.odir), options.dryRun)

        exec_me('rm %s/toys*.root' % (options.odir), options.dryRun)
        if ntoys <= 100:
            exec_me('combine -M GenerateOnly %s --rMax %s --rMin %s --toysFrequentist -t %i  --saveToys -n %s --freezeParameters %s -s %s --setParameters %s'
                    % (base, options.rMax, options.rMin, ntoys, baseName, options.freezeNuisances, options.seed, options.setParameters), options.dryRun)
            exec_me('cp higgsCombine%s.GenerateOnly.mH120.%s.root %s/' % (baseName, options.seed, options.odir), options.dryRun)
            cmd = 'combine -M GoodnessOfFit %s --rMax %s --rMin %s -t %i' \
                  + ' --toysFile %s/higgsCombine%s.GenerateOnly.mH120.%s.root --algorithm saturated -n %s --freezeParameters %s -s %s --setParameters %s'
            cmd = cmd % (base, options.rMax, options.rMin, ntoys, options.odir, baseName, options.seed, baseName, options.freezeNuisances, options.seed, options.setParameters)
            exec_me(cmd, options.dryRun)
            exec_me('cp higgsCombine%s.GoodnessOfFit.mH120.%s.root %s/toys1_%s.root' % (baseName, options.seed, options.odir, options.seed), options.dryRun)
            cmd = 'combine -M GoodnessOfFit %s --rMax %s --rMin %s -t %i ' \
                  + '--toysFile %s/higgsCombine%s.GenerateOnly.mH120.%s.root --algorithm saturated -n %s --freezeParameters %s -s %s --setParameters %s'
            cmd = cmd % (alt, options.rMax, options.rMin, ntoys, options.odir, baseName, options.seed, altName, options.freezeNuisances, options.seed, options.setParameters)
            exec_me(cmd, options.dryRun)
            exec_me('cp higgsCombine%s.GoodnessOfFit.mH120.%s.root %s/toys2_%s.root' % (altName, options.seed, options.odir, options.seed), options.dryRun)
        else:
            # if too many toys are requested, run them in parallel, 100 toys each
            nTimes = int((ntoys+1.0)/100)
            cmd_list = []
            for iT in range(nTimes):
                cmd_1 = 'combine -M GenerateOnly %s --rMax %s --rMin %s --toysFrequentist -t %i  --saveToys -n %s --freezeParameters %s -s %s --setParameters %s' \
                        % (base, options.rMax, options.rMin, 100, baseName, options.freezeNuisances, options.seed+10+iT, options.setParameters)
                cmd_2 = 'cp higgsCombine%s.GenerateOnly.mH120.%s.root %s/' % (baseName, options.seed+10+iT, options.odir)
                cmd_3 = 'combine -M GoodnessOfFit %s --rMax %s --rMin %s -t %i'
                cmd_3 += ' --toysFile %s/higgsCombine%s.GenerateOnly.mH120.%s.root --algorithm saturated -n %s --freezeParameters %s -s %s --setParameters %s'
                cmd_3 = cmd_3 % (base, options.rMax, options.rMin, 100, options.odir, baseName, options.seed+iT+10, baseName, options.freezeNuisances, options.seed+iT+10, options.setParameters)
                cmd_4 = 'cp higgsCombine%s.GoodnessOfFit.mH120.%s.root %s/toys1_%s.root' % (baseName, options.seed+iT+10, options.odir, options.seed+iT+10)
                cmd_5 = 'combine -M GoodnessOfFit %s --rMax %s --rMin %s -t %i'
                cmd_5 += ' --toysFile %s/higgsCombine%s.GenerateOnly.mH120.%s.root --algorithm saturated -n %s --freezeParameters %s -s %s --setParameters %s'
                cmd_5 = cmd_5 % (alt, options.rMax, options.rMin, 100, options.odir, baseName, options.seed+iT+10, altName, options.freezeNuisances, options.seed+iT+10, options.setParameters)
                cmd_6 = 'cp higgsCombine%s.GoodnessOfFit.mH120.%s.root %s/toys2_%s.root' % (altName, options.seed+iT+10, options.odir, options.seed+iT+10)
                cmd_this = cmd_1 + ";  " + cmd_2 + ";  " + cmd_3 + ";  " + cmd_4 + ";  " + cmd_5 + ";  " + cmd_6
                print(cmd_this)
                cmd_list.append(cmd_this)

            if not options.dryRun:
                print("now running the above commands in parallel in background...")
                procs_list = [subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,  shell=True) for cmd in cmd_list]
                for proc in procs_list:
                    proc.communicate()
                    proc.wait()
                exec_me('sleep 1; wait', options.dryRun)
                exec_me('hadd -k -f %s/toys1_%s.root %s/toys1_*.root' % (options.odir, options.seed, options.odir), options.dryRun)
                exec_me('hadd -k -f %s/toys2_%s.root %s/toys2_*.root' % (options.odir, options.seed, options.odir), options.dryRun)

    if options.dryRun:
        sys.exit()
    nllBase = fStat("%s/base1.root" % options.odir, "%s/base2.root" % options.odir, options.p1, options.p2, options.n)
    if not options.justPlot:
        print("Using these toys input %s/toys1_%s.root and %s/toys2_%s.root" % (options.odir, options.seed, options.odir, options.seed))
        nllToys = fStat("%s/toys1_%s.root" % (options.odir, options.seed), "%s/toys2_%s.root" % (options.odir, options.seed), options.p1, options.p2, options.n)
    else:
        print("Using these toys input %s/toys1_%s.root and %s/toys2_%s.root" % (options.odir, options.seed, options.odir, options.seed))
        nllToys = fStat("%s/toys1_%s.root" % (options.odir, options.seed), "%s/toys2_%s.root" % (options.odir, options.seed), options.p1, options.p2, options.n)

    lPass = 0
    for val in nllToys:
        if nllBase[0] > val:
            lPass += 1
    pval = 1
    if len(nllToys) > 0:
        pval = float(lPass)/float(len(nllToys))
        print("FTest p-value", pval)
    shortLabel = iLabel.replace("_card_rhalphabet_all", "").replace("_floatZ", "")
    plotftest(nllToys, nllBase[0], pval, shortLabel, options)
    options.algo = "saturated"
    options.method = "GoodnessOfFit"
    iLabel = 'goodness_%s_%s' % (options.algo, base.split('/')[-1].replace('.root', ''))
    goodness(base, 1000, iLabel, options)
    iLabel = 'goodness_%s_%s' % (options.algo, alt.split('/')[-1].replace('.root', ''))
    goodness(alt, 1000, iLabel, options)
    return float(lPass)/float(len(nllToys))


def goodness(base, ntoys, iLabel, options):
    exec_me('rm higgsCombine%s.GoodnessOfFit.mH120*root' % (base.split('/')[-1].replace('.root', '')), options.dryRun)
    if not options.justPlot:
        if int(options.blinded):
            exec_me('combine -M GoodnessOfFit %s  --setParameterRange r=-20,20  --setParameters %s --algorithm %s -n %s --freezeParameters %s --redefineSignalPOIs r'
                    % (base, options.setParameters, options.algo, base.split('/')[-1].replace('.root', ''), options.freezeNuisances), options.dryRun)
            exec_me('cp higgsCombine%s.GoodnessOfFit.mH120.root %s/goodbase_%s.root'
                    % (base.split('/')[-1].replace('.root', ''), options.odir, options.seed), options.dryRun)
        else:
            exec_me('combine -M GoodnessOfFit %s --algorithm %s -n %s'
                    % (base, options.algo, base.split('/')[-1].replace('.root', '')), options.dryRun)
            exec_me('cp higgsCombine%s.GoodnessOfFit.mH120.root %s/goodbase_%s.root'
                    % (base.split('/')[-1].replace('.root', ''), options.odir, options.seed), options.dryRun)
        # ToysFreq recommended for saturated, https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/part3/commonstatsmethods/#goodness-of-fit-tests
        # Default toys for other algos
        if options.algo == 'saturated':
            if ntoys <= 100:
                exec_me('combine -M GoodnessOfFit %s  --setParameterRange r=-20,20  --setParameters %s -s %i -t %i --toysFrequentist --algorithm %s -n %s --freezeParameters %s --redefineSignalPOIs r'
                        % (base, options.setParameters, options.seed, ntoys, options.algo, base.split('/')[-1].replace('.root', ''), options.freezeNuisances), options.dryRun)
            else:
                # if too many toys are requested, run them in parallel, 100 toys each
                nTimes = int((ntoys+1.0)/100)
                cmd_list = []
                for iT in range(nTimes):
                    cmd_this = 'combine -M GoodnessOfFit %s  --setParameterRange r=-20,20  --setParameters %s -s %i -t %i'
                    cmd_this += ' --toysFrequentist --algorithm %s -n %s --freezeParameters %s --redefineSignalPOIs r'
                    cmd_this = cmd_this % (base, options.setParameters, options.seed+iT+10, 100, options.algo, base.split('/')[-1].replace('.root', ''), options.freezeNuisances)
                    print(cmd_this)
                    cmd_list.append(cmd_this)
                if not options.dryRun:
                    procs_list = [subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,  shell=True) for cmd in cmd_list]
                    for proc in procs_list:
                        proc.communicate()
                        proc.wait()
                exec_me('sleep 1; wait', options.dryRun)
                exec_me('hadd -k -f higgsCombine%s.GoodnessOfFit.mH120.%s.root higgsCombine%s.GoodnessOfFit.mH120.*.root'
                        % (base.split('/')[-1].replace('.root', ''), options.seed, base.split('/')[-1].replace('.root', '')), options.dryRun)
        else:
            exec_me('combine -M GoodnessOfFit %s  --setParameterRange r=-20,20 --setParameters %s -s %i -t %i  --algorithm %s -n %s --freezeParameters %s --redefineSignalPOIs r'
                    % (base, options.setParameters, options.seed, ntoys, options.algo, base.split('/')[-1].replace('.root', ''), options.freezeNuisances), options.dryRun)
        exec_me('cp higgsCombine%s.GoodnessOfFit.mH120.%s.root %s/goodtoys_%s.root'
                % (base.split('/')[-1].replace('.root', ''), options.seed, options.odir, options.seed), options.dryRun)
    if options.dryRun and not options.justPlot:
        sys.exit()
    nllBase = goodnessVals('%s/goodbase_%s.root' % (options.odir, options.seed))
    nllToys = goodnessVals('%s/goodtoys_%s.root' % (options.odir, options.seed))
    lPass = 0
    for val in nllToys:
        if nllBase[0] > val:
            lPass += 1
    print("GoodnessOfFit p-value", float(lPass)/float(len(nllToys)))
    plotftest(nllToys, nllBase[0], float(lPass)/float(len(nllToys)), iLabel, options)
    return float(lPass)/float(len(nllToys))


def bias(base, alt, ntoys, mu, iLabel, options):
    toysOptString = ''
    if options.toysFreq:
        toysOptString = '--toysFrequentist'
    elif options.toysNoSyst:
        toysOptString = '--toysNoSystematics'

    if not options.justPlot:
        if options.scaleLumi > 0:
            # Get snapshots with lumiscale=1 for Toy generations
            snapshot_base = "combine -M MultiDimFit  %s  -n .saved " % (alt)
            snapshot_base += " -t -1 --algo none --saveWorkspace %s " % (toysOptString)
            snapshot_base += " --freezeParameters %s " % (options.freezeNuisances)
            snapshot_base += " --setParameterRange r=%s,%s:r_z=%s,%s " % (options.rMin, options.rMax, options.rMin, options.rMax)
            snapshot_base += " --setParameters lumiscale=1,%s" % options.setParameters
            exec_me(snapshot_base, options.dryRun)

        if options.scaleLumi > 0:
            # Generation toys from snapshots , setting lumiscale to 10x
            generate_base = "combine -M GenerateOnly -d higgsCombine.saved.MultiDimFit.mH120.root --snapshotName MultiDimFit "
            generate_base += " --setParameters lumiscale=%s " % (options.scaleLumi)
        else:
            generate_base = "combine -M GenerateOnly %s %s " % (alt, toysOptString)
        generate_base += " -t %s -s %s " % (ntoys, options.seed)
        generate_base += " --saveToys -n %s --redefineSignalPOIs %s" % (iLabel, options.poi)
        generate_base += " --freezeParameters %s " % (options.freezeNuisances)
        generate_base += " --setParameterRange r=%s,%s:r_z=%s,%s " % (options.rMin, options.rMax, options.rMin, options.rMax)
        generate_base += " --setParameters %s " % (options.setParameters)
        generate_base += " --trackParameters  'rgx{.*}'"
        exec_me(generate_base, options.dryRun)

        # generate and fit separately:
        fitDiag_base = "combine -M FitDiagnostics %s --toysFile higgsCombine%s.GenerateOnly.mH120.%s.root -n %s  --redefineSignalPOIs %s" % (base, iLabel, options.seed, iLabel, options.poi)
        fitDiag_base += ' --robustFit 1 --saveNLL  --saveWorkspace --setRobustFitAlgo Minuit2,Migrad'
        fitDiag_base += ' -t %s -s %s ' % (ntoys, options.seed)
        fitDiag_base += " --freezeParameters %s " % (options.freezeNuisances)
        fitDiag_base += " --setParameterRange r=%s,%s:r_z=%s,%s " % (options.rMin, options.rMax, options.rMin, options.rMax)
        if options.scaleLumi > 0:
            fitDiag_base += " --setParameters %s,lumiscale=%s " % (options.setParamters, options.scaleLumi)
        else:
            fitDiag_base += " --setParameters %s " % (options.setParameters)
        fitDiag_base += " %s " % (toysOptString)

        exec_me(fitDiag_base, options.dryRun)
        exec_me('mv  fitDiagnostics%s.root %s/biastoys_%s_%s.root' % (iLabel, options.odir, iLabel, options.seed), options.dryRun)
    if options.dryRun:
        sys.exit()
    plotgaus("%s/biastoys_%s_%s.root" % (options.odir, iLabel, options.seed), mu, "pull" + iLabel + "_" + str(options.seed), options)


def fit(base, options):
    cmd = 'combine -M MaxLikelihoodFit %s -v 2 --freezeParameters tqqeffSF,tqqnormSF'
    cmd += ' --rMin=-20 --rMax=20 --saveNormalizations --plot --saveShapes --saveWithUncertainties --minimizerTolerance 0.001 --minimizerStrategy 2'
    cmd = cmd % base
    exec_me(cmd)
    exec_me('mv mlfit.root %s/' % options.odir)
    exec_me('mv higgsCombineTest.MaxLikelihoodFit.mH120.root %s/' % options.odir)


def limit(base):
    exec_me('combine -M Asymptotic %s  ' % base)
    exec_me('mv higgsCombineTest.Asymptotic.mH120.root limits.root')


def plotmass(base, mass):
    exec_me('combine -M MaxLikelihoodFit %s --saveWithUncertainties --saveShapes' % base)
    exec_me('python plot.py --mass %s' % str(mass))


def setup(iLabel, mass, iBase, iRalph):
    exec_me('sed "s@XXX@%s@g" card_%s_tmp2.txt > %s/card_%s.txt' % (mass, iBase, iLabel, iBase))
    exec_me('cp %s*.root %s' % (iBase, iLabel))
    exec_me('cp %s*.root %s' % (iRalph, iLabel))


def setupMC(iLabel, mass, iBase):
    exec_me('mkdir %s' % iLabel)
    exec_me('sed "s@XXX@%s@g" mc_tmp2.txt > %s/mc.txt' % (mass, iLabel))
    exec_me('cp %s*.root %s' % (iBase, iLabel))


def generate(mass, toys):
    for i0 in range(0, toys):
        fileName = 'runtoy_%s.sh' % (i0)
        sub_file = open(fileName, 'a')
        sub_file.write('#!/bin/bash\n')
        sub_file.write('cd  /afs/cern.ch/user/p/pharris/pharris/public/bacon/prod/CMSSW_7_1_20/src  \n')
        sub_file.write('eval `scramv1 runtime -sh`\n')
        sub_file.write('cd - \n')
        sub_file.write('cp -r %s . \n' % os.getcwd())
        sub_file.write('cd ZQQ_%s \n' % mass)
        sub_file.write('combine -M GenerateOnly --toysNoSystematics -t 1 mc.txt --saveToys --expectSignal 1 --seed %s \n' % i0)
        sub_file.write('combine -M MaxLikelihoodFit card_ralpha.txt -t 1  --toysFile higgsCombineTest.GenerateOnly.mH120.%s.root  > /dev/null \n' % i0)
        sub_file.write('mv mlfit.root %s/mlfit_%s.root  \n' % (os.getcwd(), i0))
        sub_file.close()
        exec_me('chmod +x %s' % os.path.abspath(sub_file.name))
        exec_me('bsub -q 8nh -o out.%%J %s' % (os.path.abspath(sub_file.name)))


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('-m', '--mass', action='store', type='int', dest='mass', default=125, help='mass')
    parser.add_option('-n', '--n', action='store', type='int', dest='n', default=5*20, help='number of bins')
    parser.add_option('--p1', action='store', type='int', dest='p1', default=9, help='number of parameters for default datacard (p1 > p2)')
    parser.add_option('--p2', action='store', type='int', dest='p2', default=12, help='number of parameters for alternative datacard (p2 > p1)')
    parser.add_option('-t', '--toys', action='store', type='int', dest='toys', default=200, help='number of toys')
    parser.add_option('-s', '--seed', action='store', type='int', dest='seed', default=1, help='random seed')
    parser.add_option('--sig', action='store', type='int', dest='sig', default=1, help='sig')
    parser.add_option('-d', '--datacard', action='store', type='string', dest='datacard', default='card_rhalphabet.txt', help='datacard name')
    parser.add_option('--datacard-alt', action='store', type='string', dest='datacardAlt', default='card_rhalphabet_alt.txt', help='alternative datacard name')
    parser.add_option('--poi', action='store', type='string', dest='poi', default='r', help='poi')
    parser.add_option('-M', '--method', dest='method', default='GoodnessOfFit',
                      choices=['GoodnessOfFit', 'FTest', 'Asymptotic', 'Bias', 'MaxLikelihoodFit'], help='combine method to use')
    parser.add_option('-a', '--algo', dest='algo', default='saturated',
                      choices=['saturated', 'KS', 'AD'], help='GOF algo  to use')
    parser.add_option('-o', '--odir', dest='odir', default='plots/', help='directory to write plots and output toys', metavar='odir')
    parser.add_option('--data', action='store_true', dest='isData', default=False, help='is data')
    parser.add_option('-l', '--lumi', action='store', type='float', dest='lumi', default=137, help='lumi')
    parser.add_option('--scaleLumi', action='store', type='float', dest='scaleLumi', default=-1, help='scale nuisances by scaleLumi')
    parser.add_option('-r', '--r', dest='r', default=0, type='float', help='default value of r')
    parser.add_option('--rMin', dest='rMin', default=-20, type='float', help='minimum of r (signal strength) in profile likelihood plot')
    parser.add_option('--rMax', dest='rMax', default=20, type='float', help='maximum of r (signal strength) in profile likelihood plot')
    parser.add_option('--freezeNuisances', action='store', type='string', dest='freezeNuisances', default='None', help='freeze nuisances')
    parser.add_option('--setParameters', action='store', type='string', dest='setParameters', default='None', help='setParameters')
    parser.add_option('--pdf1', action='store', type='string', dest='pdf1', default='poly', help='fit pdf1')
    parser.add_option('--pdf2', action='store', type='string', dest='pdf2', default='poly', help='gen pdf2')
    parser.add_option('--v1n1', '--V1N1', action='store', type='int', dest='V1N1', default=2, help='order of variable 1 polynomial for fit pdf')
    parser.add_option('--v2n1', '--V2N1', action='store', type='int', dest='V2N1', default=-1, help='order of variable 2 polynomial for fit pdf')
    parser.add_option('--v1n2', '--V1N2', action='store', type='int', dest='V1N2', default=2, help='order of variale 1 polynomial for gen pdf')
    parser.add_option('--v2n2', '--V2N2', action='store', type='int', dest='V2N2', default=-1, help='order of variable 2 polynomial for gen pdf')
    parser.add_option('--dry-run', dest="dryRun", default=False, action='store_true', help="Just print out commands to run")
    parser.add_option('--just-plot', dest="justPlot", default=False, action='store_true', help="Just remake the plot")
    parser.add_option('--toysFrequentist', action='store_true', default=False, dest='toysFreq', metavar='toysFreq', help='generate frequentist toys')
    parser.add_option('--toysNoSystematics', action='store_true', default=False, dest='toysNoSyst', metavar='toysNoSyst', help='generate toys with nominal systematics')
    parser.add_option('--blinded', default=False, dest='blinded', help='run with data on SR')
    (options, args) = parser.parse_args()

    import tdrstyle
    tdrstyle.setTDRStyle()

    r.gStyle.SetOptStat(0)
    r.gStyle.SetOptFit(0)
    r.gStyle.SetOptTitle(0)
    r.gStyle.SetPaintTextFormat("1.2g")
    r.gROOT.SetBatch()
    r.RooMsgService.instance().setGlobalKillBelow(r.RooFit.FATAL)

    exec_me('mkdir -p %s' % options.odir)

    if options.method == 'GoodnessOfFit':
        iLabel = 'goodness_%s_%s' % (options.algo, options.datacard.split('/')[-1].replace('.root', ''))
        goodness(options.datacard, options.toys, iLabel, options)

    elif options.method == 'MaxLikelihoodFit':
        fit(options.datacard, options)

    elif options.method == 'FTest':
        iLabel = 'ftest_%s_vs_%s' % (options.datacard.split('/')[-1].replace('.root', ''),
                                     options.datacardAlt.split('/')[-1].replace('.root', ''))
        ftest(options.datacard, options.datacardAlt, options.toys, iLabel, options)
    elif options.method == 'Bias':
        iLabel = 'bias_%s%i%i_vs_%s%i%i_%s%i' % (options.pdf1, options.V1N1,
                                                 options.V2N1, options.pdf2,
                                                 options.V1N2, options.V2N2,
                                                 options.poi, options.r)
        bias(options.datacard, options.datacardAlt, options.toys, options.r, iLabel, options)
