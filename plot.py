#! /usr/bin/env python
import ROOT as r,sys,math,array,os
from optparse import OptionParser
from ROOT import std,RooDataHist
from array import array
#sys.path.insert(0, '../.')
import tdrstyle
tdrstyle.setTDRStyle()

parser = OptionParser()
parser.add_option('--input'  ,action='store',type='string',dest='input'    ,default='mlfit.root',help='input file')
parser.add_option('--data'   ,action='store',type='string',dest='data'     ,default='results/base.root',help='data file')
parser.add_option('--cats'    ,action='store',type='string',dest='cats'    ,default='1,2,3,4',help='categories 0,1,2,...')
parser.add_option('--passfail',action='store_true',         dest='passfail',default=True,help='fit pass and failng') 
parser.add_option('--divide'  ,action='store_true',         dest='divide'  ,default=False,help='ratio') 
parser.add_option('--mass'    ,action='store',              dest='mass'    ,default=100  ,help='mass') 

(options,args) = parser.parse_args()

def end():
    if __name__ == '__main__':
        rep = ''
        while not rep in [ 'q', 'Q','a',' ' ]:
            rep = raw_input( 'enter "q" to quit: ' )
            if 1 < len(rep):
                rep = rep[0]

def divide(iData,iHists):
    lPass = -1
    lFail = -1
    for i0 in range(0,len(iHists)):
        if iHists[i0].GetName().find("pass") > -1 and lPass == -1:
            lPass = i0
        if iHists[i0].GetName().find("fail") > -1 and lFail == -1:
            lFail = i0
    if lPass != -1:
        iData[0].Divide(iHists[lPass])
        for i0 in range(0,len(iHists)):
            if i0 != lPass and iHists[i0].GetName().find("pass") > -1:
                iHists[i0].Divide(iHists[lPass])
        iHists[lPass].Divide(iHists[lPass])

    if lFail != -1:
        iData[1].Divide(iHists[lFail])
        for i0 in range(0,len(iHists)):
            if i0 != lFail and iHists[i0].GetName().find("fail") > -1:
                iHists[i0].Divide(iHists[lFail])
        iHists[lFail].Divide(iHists[lFail])

def draw(iData,iHists,iName="A",iPF=True,iDivide=False):
    iSumHP = iHists[0].Clone()
    iSumHP.Add(iHists[1])
    iSumHP.Add(iHists[2])
    iSumHP.Add(iHists[3])
    ksScoreP = iData[0].KolmogorovTest( iSumHP )
    chiScoreP = iData[0].Chi2Test( iSumHP , "UWCHI2/NDF CHI2 P")
    print 'chiscore ',chiScoreP
    print 'ksscore ',ksScoreP

    if iDivide:
        divide(iData,iHists)
        iData[0].GetYaxis().SetRangeUser(0.6,1.4)
        iData[1].GetYaxis().SetRangeUser(0.9,1.1)
    lC0 = r.TCanvas("Can"+iName,"Can"+iName,800,600);
    if iPF:
        lC0.Divide(2)
    lC0.cd(1)
    pDraw=False
    for pHist in iHists:
        if pHist.GetName().find("pass") > -1:
            pHist.Draw("hist sames") if pDraw else pHist.Draw("e2 sames")
            pDraw=True
    iData[0].Draw("ep sames")
    lLegend = r.TLegend(0.63,0.63,0.88,0.88)
    if iDivide:
        lLegend = r.TLegend(0.23,0.23,0.48,0.48)
    lLegend.SetFillColor(0)
    lLegend.SetBorderSize(0)
    lLegend.AddEntry(iData [0],"data","lp")
    lLegend.AddEntry(iHists[0],"QCD","lf")
    lLegend.AddEntry(iHists[1],"W#rightarrow qq","l")
    lLegend.AddEntry(iHists[2],"Z#rightarrow qq","l")
    lLegend.AddEntry(iHists[3],"top","l")
    lLegend.AddEntry(iHists[4],"Signal","lf")
    lLegend.Draw()
    tag4 = r.TLatex(0.57,0.52,"#chi2 = %.2f"%chiScoreP)
    tag4.SetNDC()
    tag4.SetTextSize(0.030)
    tag4.Draw()
    tag5 = r.TLatex(0.57,0.42,"ks = %.2f"%ksScoreP)
    tag5.SetNDC()
    tag5.SetTextSize(0.030)
    tag5.Draw()
    if not iPF:
        lC0.SaveAs(iName+".png")
        lC0.SaveAs(iName+".pdf")
        lC0.SaveAs(iName+".C")
        end()
        return

    lC0.cd(2)
    iData[1].Draw("ep")
    pDraw=False
    for pHist in iHists:
        if pHist.GetName().find("fail") > -1:
            pHist.Draw("hist sames") if pDraw else pHist.Draw("e2 sames")
            pDraw=True
    lC0.Modified()
    lC0.Update()
    iData[1].Draw("ep sames")
    lC0.SaveAs(iName+".png")
    lC0.SaveAs(iName+".pdf")
    lC0.SaveAs(iName+".C")
    end()

def norm(iFile,iH,iName) :
    lNorms = iName.split("/")[0].replace("shapes","norm")
    lArg = iFile.Get(lNorms)
    lName = iName.replace(iName.split("/")[0]+"/","")
    #print "!!!",lName,lNorms
    lVal = r.RooRealVar(lArg.find(lName)).getVal();
    iH.Scale(lVal/iH.Integral())
    
def load(iFile,iName,iNorm=True):
    lHist = iFile.Get(iName)
    if iNorm:
        norm(iFile,lHist,iName)
    lHist.SetName(iName.replace("/","_"))
    lHist.SetTitle(iName.replace("/","_"))
    return lHist
    
def loadHist(iFile,iCat,iMass,iEWK=True,iS=True):
    lHists = []
    lFit = "shapes_fit_s/"+iCat+"/" if iS else "shapes_fit_b/"+iCat+"/"
    #lFit = "shapes_prefit/"+iCat+"/" 
    lHists.append(load(iFile,lFit+"qcd"))
    lHists[0].SetFillColor(16)
    lHists[0].SetFillStyle(3001)
    lHists[0].SetLineStyle(2)
    if iEWK:
        lId = len(lHists)
        lHists.append(load(iFile,lFit+"wqq"))
        lHists.append(load(iFile,lFit+"zqq"))
        lHists.append(load(iFile,lFit+"tqq"))
        #lHists.append(load(iFile,lFit+"zqq"+str(iMass)))
        lHists[lId].SetLineColor(46)
        lHists[lId+1].SetLineColor(9)
        lHists[lId+2].SetLineColor(8)
        #lHists[lId+3].SetLineColor(r.kOrange)
        for i0 in range(lId,lId+3):
            lHists[i0].SetLineWidth(2)
            lHists[i0].Add(lHists[i0-1])
    return lHists

def loadData(iDataFile,iCat):
    #lW = iDataFile.Get("w_"+iCat)
    #lData = lW.data("data_obs_"+iCat).createHistogram("x")
    lData = load(iDataFile,"shapes_fit_s/"+str(iCat)+"/data",False)
    #lData = load(iDataFile,"shapes_prefit/"+str(iCat)+"/data",False)
    lData.GetXaxis().SetTitle("m_{J} (GeV)")
    lData.SetMarkerStyle(20)
    return [lData]

def hist(iData):
    lX = []
    for i0 in range(iData.GetN()):
        lX.append(-iData.GetErrorXlow(i0)+iData.GetX()[i0])
    lX.append(iData.GetX()[iData.GetN()-1]+iData.GetErrorXhigh(iData.GetN()-1))
    lHist = r.TH1F("dataSum","dataSum",iData.GetN(),array('d',lX))
    lHist.Sumw2()
    return lHist

def add(iSum,iData):
    for i0 in range(iData.GetN()):
        iSum.Fill(iData.GetX()[i0],iData.GetY()[i0]*(iData.GetErrorXlow(i0)+iData.GetErrorXhigh(i0)))
        #iSum.SetBinContent(i0,iSum.GetBinContent(i0)+iData.GetY()[i0])
    for i0 in range(1,iSum.GetNbinsX()+1):
        iSum.SetBinError(i0,math.sqrt(iSum.GetBinContent(i0)))
    return iSum

if __name__ == "__main__":
    lHFile = r.TFile(options.input)
    lDFile = r.TFile(options.input)
    lDSum=[]
    lSum=[]
    iC=0
    for cat in options.cats.split(','):
        iC=iC+1
        #lData  = loadData(lDFile,"pass_cat"+cat)
        lData  = loadData(lDFile,"ch"+str(cat)+"_pass_cat"+cat)
        lHists = loadHist(lHFile,"ch"+str(cat)+"_pass_cat"+cat,options.mass)
        #lHists = loadHist(lHFile,"pass_cat"+cat,options.mass)
        if options.passfail:
            lData .extend(loadData(lDFile,"ch"+str(cat)+"_fail_cat"+cat))
            lHists.extend(loadHist(lHFile,"ch"+str(cat)+"_fail_cat"+cat,options.mass,True,True))
            #lHists.extend(loadHist(lHFile,"fail_cat"+cat,options.mass,True,True))
        if len(lSum) == 0:
            lDSum = [hist(lData[0]),hist(lData[1])]
            for i0 in range(0,len(lDSum)):
                add(lDSum[i0],lData[i0])
            lSum  = lHists
        else:
            for i0 in range(0,len(lDSum)):
                add(lDSum[i0],lData[i0])
                print i0,lDSum[i0].Integral()
            for i0 in range(0,len(lSum)):
                lSum[i0].Add(lHists[i0])
                print i0,lHists[i0].Integral()
        #draw(lData,lHists,cat,options.passfail,options.divide)
    draw(lDSum,lSum,"sum",options.passfail,options.divide)

