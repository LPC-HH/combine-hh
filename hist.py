#! /usr/bin/env python
import ROOT as r,sys,math,array

class hist:
    def __init__( self , iVars, iHists):
        self._vals  = iVars
        self._hists = iHists
        self._mass  = r.RooRealVar("x","x",iHists[0].GetXaxis().GetXmin(),iHists[0].GetXaxis().GetXmax())
        self._mass.setBins(iHists[0].GetNbinsX())
        self._dhist = []
        self._hpdf  = []
                
    def histpdf(self,iH,iShift=0):
        lDH    = r.RooDataHist(iH.GetName()+"d0" ,iH.GetName()+"d0" ,r.RooArgList(self._mass),iH)
        if iShift != 0:
            lHPdf  = r.RooHistPdf (iH.GetName()+"dh0",iH.GetName()+"dh0",r.RooArgList(iShift),r.RooArgList(self._mass),lDH)
        else:
            lHPdf  = r.RooHistPdf (iH.GetName()+"dh0",iH.GetName()+"dh0",r.RooArgSet(self._mass),lDH)
        self._dhist.extend([lDH])
        self._hpdf .extend([lHPdf])
        return lHPdf
        
    def morph(self,iValue):
        lMarker=0
        for pVal in self._vals:
            if pVal > iValue:
                break
            lMarker=lMarker+1
        lVal   = iValue-self._vals[lMarker-1]
        lVal  /= float(abs(self._vals[lMarker]-self._vals[lMarker-1]))
        lMed   = r.RooRealVar("med","med",0,1)
        lRH0   = self.histpdf(self._hists[lMarker])
        lRH1   = self.histpdf(self._hists[lMarker-1])
        lMorph = r.RooIntegralMorph("Morph","Morph",lRH0,lRH1,self._mass,lMed)
        lMed.setVal(lVal);
        lOut   = lMorph.createHistogram("tmp"+str(iValue),self._mass)
        lInt   = (self._hists[lMarker].Integral()-self._hists[lMarker-1].Integral())*lVal+self._hists[lMarker-1].Integral()
        lOut.Scale(lInt)
        return lOut

    def shift(self,iH,iScale):
        lDM     = r.RooRealVar("dm","dm", 0.,-50,50)
        lShift  = r.RooFormulaVar("shift","x-dm",r.RooArgList(self._mass,lDM))  
        lHPdf = self.histpdf(iH,lShift)
        lDM.setVal(iScale)
        lUp = lHPdf.createHistogram("x")
        lUp.SetTitle(lHPdf.GetName()+"_scaleUp")
        lUp.SetName (lHPdf.GetName()+"_scaleUp")
        lUp.Scale(iH.Integral())
        
        lDM.setVal(-iScale)
        lDown = lHPdf.createHistogram("x")
        lDown.SetTitle(lHPdf.GetName()+"_scaleDown")
        lDown.SetName (lHPdf.GetName()+"_scaleDown")
        lDown.Scale(iH.Integral())
        return [lUp,lDown]
    
    def smear(self,iH,iScale):
        lDM     = r.RooRealVar("dm","dm", 1.,0.,2.)
        lShift  = r.RooFormulaVar("shift","("+self._mass.GetName()+"-"+str(iH.GetMean())+")/dm+"+str(iH.GetMean()),r.RooArgList(self._mass,lDM))  
        lHPdf = self.histpdf(iH,lShift)
        lDM.setVal(1.+iScale)
        lUp = lHPdf.createHistogram("x")
        lUp.SetTitle(lHPdf.GetName()+"_smearUp")
        lUp.SetName (lHPdf.GetName()+"_smearUp")
        lUp.Scale(iH.Integral())
                
        lDM.setVal(1.-iScale)
        lDown = lHPdf.createHistogram("x")
        lDown.SetTitle(lHPdf.GetName()+"_smearDown")
        lDown.SetName (lHPdf.GetName()+"_smearDown")
        lDown.Scale(iH.Integral())
        return [lUp,lDown]

def uncorrelate(hists, sysName, suppressLevel=None):
    """Replaces each histogram whose name contains 'sysName' with many copies that represent uncorrelated bin-by-bin systematics.
    suppressLevel: if provided, new histograms will only be created for bins that differ from nominal by a fractional amount greater than suppressLevel."""
    #get all histograms that match the input string
    toUncorrelate = [name for name in hists if sysName in name]
    print "Treating the following distributions as uncorrelated for",sysName,": "
    for name in toUncorrelate: print name
    
    #get names of individual systematics
    systNames = []
    for name in toUncorrelate:
        systName = name.replace("Up","").replace("Down","")
        if systName not in systNames:
            systNames.append(systName)

    for name in systNames:
        print("Uncorrelating "+name)
        #get histogram with central values
        centerName = name.split("_")[:-1]
        centerName = '_'.join(centerName)
        #get up and down variants
        upName = name+'Up'
        downName = name+'Down'
        uncName = name.split("_")[-1]
        print("Central values taken from "+centerName)
        #for each bin create a new histogram in which that bin is up/down and the rest are centered
        for b in range(1,hists[centerName].GetNbinsX()+1):
            newHistUpName = centerName+"_"+uncName+str(b)+"Up"
            newHistDownName = centerName+"_"+uncName+str(b)+"Down"

            #check level of agreement with the nominal
            if suppressLevel is not None:
                #get percent difference from nominal
                if hists[centerName].GetBinContent(b) > 0:
                    percDifferenceUp = abs(hists[upName].GetBinContent(b)-hists[centerName].GetBinContent(b))/hists[centerName].GetBinContent(b)
                    percDifferenceDown = abs(hists[downName].GetBinContent(b)-hists[centerName].GetBinContent(b))/hists[centerName].GetBinContent(b)
                    percDifference = max(percDifferenceUp, percDifferenceDown)
                    if percDifference <= suppressLevel: 
                        #print "Suppressing nuisance in bin",b,"(agrees at",percDifference,"level)"
                        continue
                elif hists[upName].GetBinContent(b) == hists[centerName].GetBinContent(b) and hists[downName].GetBinContent(b) == hists[centerName].GetBinContent(b): 
                        #print "Suppressing nuisance in bin",b,"because there is no change from the nominal"
                        continue

            #new up histogram
            hists[newHistUpName] = hists[centerName].Clone(newHistUpName)
            hists[newHistUpName].SetDirectory(0)
            hists[newHistUpName].SetBinContent(b, hists[upName].GetBinContent(b)) #new hist has the unperturbed value in every bin except one
            hists[newHistUpName].SetBinError(b, hists[upName].GetBinError(b))

            #new down histogram
            hists[newHistDownName] = hists[centerName].Clone(newHistDownName)
            hists[newHistDownName].SetDirectory(0)
            hists[newHistDownName].SetBinContent(b, hists[downName].GetBinContent(b)) #new hist has the unperturbed value in every bin except one
            hists[newHistDownName].SetBinError(b, hists[downName].GetBinError(b))

        #remove the original histogram
        del hists[upName]
        del hists[downName]
