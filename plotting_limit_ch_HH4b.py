# ref: https://github.com/chernyavskaya/flashggFinalFit/blob/fullRunII_unblindedGGF/Plots/FinalResults/plot_c2v_scan.py
from optparse import OptionParser
# from ROOT import *
import ROOT
ROOT.gROOT.SetBatch(True)


def redrawBorder():
    # this little macro redraws the axis tick marks and the pad border lines.
    ROOT.gPad.Update()
    ROOT.gPad.RedrawAxis()
    line = ROOT.TLine()
    line.SetLineWidth(3)
    line.DrawLine(ROOT.gPad.GetUxmin(), ROOT.gPad.GetUymax(), ROOT.gPad.GetUxmax(), ROOT.gPad.GetUymax())
    line.DrawLine(ROOT.gPad.GetUxmax(), ROOT.gPad.GetUymin(), ROOT.gPad.GetUxmax(), ROOT.gPad.GetUymax())
    line.DrawLine(ROOT.gPad.GetUxmin(), ROOT.gPad.GetUymin(), ROOT.gPad.GetUxmin(), ROOT.gPad.GetUymax())
    line.DrawLine(ROOT.gPad.GetUxmin(), ROOT.gPad.GetUymin(), ROOT.gPad.GetUxmax(), ROOT.gPad.GetUymin())


def getVals(fname):
    fIn = ROOT.TFile.Open(fname)
    vals = []
    if fIn:
        tIn = fIn.Get('limit')
        if tIn.GetEntries() < 5:
            print "*** WARNING: cannot parse file", fname, "because nentries != 5"
            raise RuntimeError('cannot parse file')
        for i in range(0, tIn.GetEntries()):
            tIn.GetEntry(i)
            qe = tIn.quantileExpected
            lim = tIn.limit
            vals.append((qe, lim))
    else:
        vals = -1
    return vals


def ych_label(name, yvalue):
    pt_l1 = ROOT.TPaveText(0.05, yvalue, 0.1, yvalue+0.1, "brNDC")
    pt_l1.SetBorderSize(0)
    pt_l1.SetFillColor(0)
    pt_l1.SetTextSize(0.040)
    pt_l1.SetTextFont(42)
    pt_l1.SetFillStyle(0)
    pt_l1.AddText(name)
    return pt_l1


def set_style(grexp, grobs, gr1sigma, gr2sigma):
    # set styles
    grexp.SetMarkerStyle(24)
    grexp.SetMarkerColor(4)
    grexp.SetMarkerSize(0.8)
    grexp.SetLineColor(ROOT.kBlue+2)
    grexp.SetLineWidth(3)
    grexp.SetLineStyle(2)
    grexp.SetFillColor(0)

    grobs.SetLineColor(1)
    grobs.SetLineWidth(3)
    grobs.SetMarkerColor(1)
    grobs.SetMarkerStyle(20)
    grobs.SetFillStyle(0)

    gr1sigma.SetMarkerStyle(0)
    gr1sigma.SetMarkerColor(3)
    gr1sigma.SetFillColor(ROOT.kGreen+1)
    gr1sigma.SetLineColor(ROOT.kGreen+1)
    gr1sigma.SetFillStyle(1001)

    # gr2sigma.SetName(tooLopOn[ic])
    gr2sigma.SetMarkerStyle(0)
    gr2sigma.SetMarkerColor(5)
    gr2sigma.SetFillColor(ROOT.kOrange)
    gr2sigma.SetLineColor(ROOT.kOrange)
    gr2sigma.SetFillStyle(1001)


################################################################################################
# OPTIONS
parser = OptionParser()
parser.add_option("--whatToFloat", default='r', help="what to float")
parser.add_option("--inputtag", help="tag")
parser.add_option("--unblind", default=False, help="Observed is present or not ")
(options, args) = parser.parse_args()
###########
# CREATE TAGS

print("options: options.whatToFloat=", options.whatToFloat)

datalumi = "138 fb^{-1} (13 TeV)"

xmin = 1
xmax = 201
ymin = 0
ymax = 6
inter = 1
num_location = 0.88

ylable_text = ["Combined", "Category 1", "Category 2", "Category 3"]

Nch = 4  # len(ylable_text)
print("N: ", Nch)

if not options.unblind:
    dirnames = [
        "higgsCombine"+options.inputtag+".AsymptoticLimits.mH125.123456.root",
        "higgsCombine"+options.inputtag+"_Bin1.AsymptoticLimits.mH125.123456.root",
        "higgsCombine"+options.inputtag+"_Bin2.AsymptoticLimits.mH125.123456.root",
        "higgsCombine"+options.inputtag+"_Bin3.AsymptoticLimits.mH125.123456.root"
    ]
else:
    dirnames = [
        "higgsCombine"+options.inputtag+".AsymptoticLimits.mH125.root",
        "higgsCombine"+options.inputtag+"_Bin1.AsymptoticLimits.mH125.root",
        "higgsCombine"+options.inputtag+"_Bin2.AsymptoticLimits.mH125.root",
        "higgsCombine"+options.inputtag+"_Bin3.AsymptoticLimits.mH125.root"
    ]

pt_channel_names = []
for ich in range(Nch):
    pt_channel_names.append(ych_label(ylable_text[ich], 0.2+ich*0.1))

c1 = ROOT.TCanvas("c1", "c1", 650, 500)
c1.SetFrameLineWidth(3)
c1.SetBottomMargin(0.15)
c1.SetRightMargin(0.05)
c1.SetLeftMargin(0.15)

ROOT.gPad.SetLogx(1)
mg = ROOT.TMultiGraph()

gr2sigma = ROOT.TGraphAsymmErrors()
gr1sigma = ROOT.TGraphAsymmErrors()
grexp = ROOT.TGraph()
grobs = ROOT.TGraph()
graph = ROOT.TGraph()

gr2sigma_ch2 = ROOT.TGraphAsymmErrors()
gr1sigma_ch2 = ROOT.TGraphAsymmErrors()
grexp_ch2 = ROOT.TGraph()
grobs_ch2 = ROOT.TGraph()
graph_ch2 = ROOT.TGraph()

gr2sigma_ch3 = ROOT.TGraphAsymmErrors()
gr1sigma_ch3 = ROOT.TGraphAsymmErrors()
grexp_ch3 = ROOT.TGraph()
grobs_ch3 = ROOT.TGraph()
graph_ch3 = ROOT.TGraph()

gr2sigma_ch4 = ROOT.TGraphAsymmErrors()
gr1sigma_ch4 = ROOT.TGraphAsymmErrors()
grexp_ch4 = ROOT.TGraph()
grobs_ch4 = ROOT.TGraph()
graph_ch4 = ROOT.TGraph()

ptsList = []  # (x, obs, exp, p2s, p1s, m1s, m2s)

k = 0
for ich in range(Nch):
    print("ich:", ich)
    fname = dirnames[ich]
    vals = getVals(fname)
    if vals == -1:
        continue

    if not options.unblind:
        obs = 0.0  # FIXME
    else:
        obs = vals[5][1]

    m2s_t = vals[0][1]
    m1s_t = vals[1][1]
    exp = vals[2][1]
    p1s_t = vals[3][1]
    p2s_t = vals[4][1]

    # because the other code wants +/ sigma vars as deviations, without sign, from the centeal exp value...
    p2s = p2s_t - exp
    p1s = p1s_t - exp
    m2s = exp - m2s_t
    m1s = exp - m1s_t
    xval = ich

    ptsList.append((xval, obs, exp, p2s_t, p1s_t, m1s_t, m2s_t))
    k = k+1

print("ptsList: ", ptsList)
for ipt, pt in enumerate(ptsList):
    xval = pt[0]
    obs = pt[1]
    exp = pt[2]
    p2s = pt[3]
    p1s = pt[4]
    m1s = pt[5]
    m2s = pt[6]
    print("pt:", pt)
    if ipt == 0:
        grexp.SetPoint(0, exp, xval)
        grexp.SetPoint(1, exp, xval+1)
        grobs.SetPoint(0, obs, xval)
        grobs.SetPoint(1, obs, xval+1)
        gr1sigma.SetPoint(0, m1s, xval+0.5)
        gr1sigma.SetPoint(1, p1s, xval+0.5)
        gr2sigma.SetPoint(0, m2s, xval+0.5)
        gr2sigma.SetPoint(1, p2s, xval+0.5)
        gr1sigma.SetPointError(0, 0, 0, 0.5, 0.5)
        gr1sigma.SetPointError(1, 0, 0, 0.5, 0.5)
        gr2sigma.SetPointError(0, 0, 0, 0.5, 0.5)
        gr2sigma.SetPointError(1, 0, 0, 0.5, 0.5)
    elif ipt == 1:
        grexp_ch2.SetPoint(0, exp, xval)
        grexp_ch2.SetPoint(1, exp, xval+1)
        grobs_ch2.SetPoint(0, obs, xval)
        grobs_ch2.SetPoint(1, obs, xval+1)
        gr1sigma_ch2.SetPoint(0, m1s, xval+0.5)
        gr1sigma_ch2.SetPoint(1, p1s, xval+0.5)
        gr2sigma_ch2.SetPoint(0, m2s, xval+0.5)
        gr2sigma_ch2.SetPoint(1, p2s, xval+0.5)
        gr1sigma_ch2.SetPointError(0, 0, 0, 0.5, 0.5)
        gr1sigma_ch2.SetPointError(1, 0, 0, 0.5, 0.5)
        gr2sigma_ch2.SetPointError(0, 0, 0, 0.5, 0.5)
        gr2sigma_ch2.SetPointError(1, 0, 0, 0.5, 0.5)
    elif ipt == 2:
        grexp_ch3.SetPoint(0, exp, xval)
        grexp_ch3.SetPoint(1, exp, xval+1)
        grobs_ch3.SetPoint(0, obs, xval)
        grobs_ch3.SetPoint(1, obs, xval+1)
        gr1sigma_ch3.SetPoint(0, m1s, xval+0.5)
        gr1sigma_ch3.SetPoint(1, p1s, xval+0.5)
        gr2sigma_ch3.SetPoint(0, m2s, xval+0.5)
        gr2sigma_ch3.SetPoint(1, p2s, xval+0.5)
        gr1sigma_ch3.SetPointError(0, 0, 0, 0.5, 0.5)
        gr1sigma_ch3.SetPointError(1, 0, 0, 0.5, 0.5)
        gr2sigma_ch3.SetPointError(0, 0, 0, 0.5, 0.5)
        gr2sigma_ch3.SetPointError(1, 0, 0, 0.5, 0.5)
    else:
        grexp_ch4.SetPoint(0, exp, xval)
        grexp_ch4.SetPoint(1, exp, xval+1)
        grobs_ch4.SetPoint(0, obs, xval)
        grobs_ch4.SetPoint(1, obs, xval+1)
        gr1sigma_ch4.SetPoint(0, m1s, xval+0.5)
        gr1sigma_ch4.SetPoint(1, p1s, xval+0.5)
        gr2sigma_ch4.SetPoint(0, m2s, xval+0.5)
        gr2sigma_ch4.SetPoint(1, p2s, xval+0.5)
        gr1sigma_ch4.SetPointError(0, 0, 0, 0.5, 0.5)
        gr1sigma_ch4.SetPointError(1, 0, 0, 0.5, 0.5)
        gr2sigma_ch4.SetPointError(0, 0, 0, 0.5, 0.5)
        gr2sigma_ch4.SetPointError(1, 0, 0, 0.5, 0.5)

print("check0")

# Create functions from median expected and observed

set_style(grexp, grobs, gr1sigma, gr2sigma)
set_style(grexp_ch2, grobs_ch2, gr1sigma_ch2, gr2sigma_ch2)
set_style(grexp_ch3, grobs_ch3, gr1sigma_ch3, gr2sigma_ch3)
set_style(grexp_ch4, grobs_ch4, gr1sigma_ch4, gr2sigma_ch4)

mg.Add(gr2sigma, "3")
mg.Add(gr1sigma, "3")
mg.Add(grexp, "L")
mg.Add(grobs, "L")

mg.Add(gr2sigma_ch2, "3")
mg.Add(gr1sigma_ch2, "3")
mg.Add(grexp_ch2, "L")
mg.Add(grobs_ch2, "L")

mg.Add(gr2sigma_ch3, "3")
mg.Add(gr1sigma_ch3, "3")
mg.Add(grexp_ch3, "L")
mg.Add(grobs_ch3, "L")

print("check1")
###########
legend = ROOT.TLegend(0, 0, 0, 0)
legend.SetNColumns(2)
legend.SetX1(0.2)
legend.SetY1(0.75)
legend.SetX2(0.8)
legend.SetY2(0.88)

legend.SetFillColor(ROOT.kWhite)
legend.SetBorderSize(0)
# legend
legend.SetHeader('95% CL upper limit')
legend.AddEntry(grobs, "Observed", "l")
legend.AddEntry(gr1sigma, "68% expected", "f")
legend.AddEntry(grexp, "Median expected", "l")
legend.AddEntry(gr2sigma, "95% expected", "f")

# text
pt = ROOT.TPaveText(0.1663218-0.02, 0.886316, 0.3045977-0.02, 0.978947, "brNDC")
pt.SetBorderSize(0)
pt.SetTextAlign(12)
pt.SetTextFont(62)
pt.SetTextSize(0.05)
pt.SetFillColor(0)
pt.SetFillStyle(0)
pt.AddText("CMS #font[52]{Internal}")

pt2 = ROOT.TPaveText(0.79, 0.9066667, 0.8997773, 0.957037, "brNDC")
pt2.SetBorderSize(0)
pt2.SetFillColor(0)
pt2.SetTextSize(0.040)
pt2.SetTextFont(42)
pt2.SetFillStyle(0)
pt2.AddText(datalumi)

ROOT.gStyle.SetPaintTextFormat("4.0f")

hframe = ROOT.TH2F('hframe', "", 10, xmin, xmax, 10, 0, 10)
hframe.SetStats(0)

for ich in range(Nch):
    if options.unblind:
        hframe.Fill(num_location*xmax, ylable_text[ich], ptsList[ich][1])
    else:
        hframe.Fill(num_location*xmax, ylable_text[ich], ptsList[ich][2])
hframe.LabelsDeflate("Y")
hframe.LabelsOption("v")

hframe.GetYaxis().SetTitleSize(0)
hframe.GetXaxis().SetTitleSize(0.055)
hframe.SetMarkerSize(1.8)
hframe.GetYaxis().SetLabelSize(0.05)
hframe.GetXaxis().SetLabelSize(0.045)
hframe.GetXaxis().SetLabelOffset(0.012)
hframe.GetYaxis().SetTitleOffset(1.2)
hframe.GetXaxis().SetTitleOffset(1.1)

hframe.GetYaxis().SetTitle("")
hframe.GetXaxis().SetTitle(r"\sigma_{HH}/\sigma_{SM_{HH}}")

hframe.Draw("text")
hframe.GetYaxis().SetRangeUser(0, Nch+100)

gr2sigma.Draw("3same")
gr1sigma.Draw("3same")
grexp.Draw("Lsame")

gr2sigma_ch2.Draw("3same")
gr1sigma_ch2.Draw("3ssame")
grexp_ch2.Draw("Lsame")

gr2sigma_ch3.Draw("3same")
gr1sigma_ch3.Draw("3ssame")
grexp_ch3.Draw("Lsame")

gr2sigma_ch4.Draw("3same")
gr1sigma_ch4.Draw("3ssame")
grexp_ch4.Draw("Lsame")

if options.unblind:
    grobs.Draw("Lsame")
    grobs_ch2.Draw("Lsame")
    grobs_ch3.Draw("Lsame")
    grobs_ch4.Draw("Lsame")
pt.Draw()
pt2.Draw()
c1.Update()
c1.RedrawAxis()
legend.Draw()

c1.Update()
c1.Print('limit_ch_test_%s_to_%s.pdf' % (options.inputtag, options.whatToFloat), 'pdf')
c1.Print('limit_ch_test_%s_to_%s.png' % (options.inputtag, options.whatToFloat), 'png')
