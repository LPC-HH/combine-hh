#!/bin/bash
dataset=data_obs
version=$1
inputdir=$2
ws=HHModel_combined_${version}
postfitws=higgsCombineSnapshot_${version}.MultiDimFit.mH125.root

combineCards.py fitfail=cards_Bin1/HHModel/fitfail.txt fail=cards_Bin1/HHModel/fail.txt SRBin1=cards_Bin1/HHModel/SRBin1.txt SRBin2=cards_Bin2/HHModel/SRBin2.txt SRBin3=cards_Bin3/HHModel/SRBin3.txt passBin1=cards_Bin1/HHModel/passBin1.txt passBin2=cards_Bin2/HHModel/passBin2.txt passBin3=cards_Bin3/HHModel/passBin3.txt > ${ws}.txt

text2workspace.py ${ws}.txt -P HiggsAnalysis.CombinedLimit.hh_model:model_default --channel-masks --mass=125

#need to perform bkg-only fit first to have data-drive QCD+ggH+VBF bkg fit, and in the next step use this snapshot to generate Asimove dataset
echo "bkg-only fit"
combine -D $dataset -M MultiDimFit --saveWorkspace -m 125 ${ws}.root  --cminDefaultMinimizerStrategy 1 --setParameters mask_SRBin1=1,mask_SRBin2=1,mask_SRBin3=1,mask_SRfail=1,mask_fail=1,r=0 --freezeParameters r,r_gghh,r_qqhh,kt,kl,CV,C2V -n Snapshot_${version} --verbose -1

#echo "prepare datacard for HH combination"
# https://cms-b2g.docs.cern.ch/combine/StatTests/
# https://twiki.cern.ch/twiki/bin/view/CMS/SWGuideHiggsAnalysisCombinedLimit
# https://twiki.cern.ch/twiki/bin/view/CMS/HiggsWG/HiggsPAGPreapprovalChecks
# ws for HH combination
combine -M FitDiagnostics -d ${ws}.root --rMin 0 --rMax 4 -n Bkgonly_${version} --cminDefaultMinimizerStrategy 1 --setParameters mask_SRBin1=1,mask_SRBin2=1,mask_SRBin3=1,mask_fail=1,r=0 --freezeParameters r_gghh,r_qqhh,kt,kl,CV,C2V --saveNormalizations --saveShapes --saveOverallShapes --ignoreCovWarning --saveWorkspace --redefineSignalPOIs r
python ../script/diffNuisances.py -a fitDiagnosticsbkgonly${version}.root --skipFitS -g plots.root

#echo "fit kl"
combine -M MultiDimFit -t -1 ${postfitws} --snapshotName MultiDimFit --bypassFrequentistFit --redefineSignalPOIs kl --setParameters r=1,r_gghh=1,r_qqhh=1,kt=1,kl=1,CV=1,C2V=1,mask_SRBin1=0,mask_SRBin2=0,mask_SRBin3=0,mask_fitfail=0,mask_passBin1=1,mask_passBin2=1,mask_passBin3=1,mask_fail=1 --toysFrequentist -m 125 -n kl_bestfit_${version} --freezeParameters r,r_gghh,r_qqhh,kt,CV,C2V --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1

echo "expected kl 1D scan"
combine -M MultiDimFit -t -1 --algo grid --point 45 ${postfitws} --snapshotName MultiDimFit --bypassFrequentistFit --redefineSignalPOIs kl --setParameters r=1,r_gghh=1,r_qqhh=1,kt=1,kl=1,CV=1,C2V=1,mask_SRBin1=0,mask_SRBin2=0,mask_SRBin3=0,mask_fitfail=0,mask_passBin1=1,mask_passBin2=1,mask_passBin3=1,mask_fail=1 --toysFrequentist -m 125 -n kl_scan_${version} --setParameterRanges kl=-18.5,26.5 --freezeParameters r,r_gghh,r_qqhh,kt,CV,C2V --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1

python ../../../script/plot1DScan.py higgsCombinekl_scan_${version}.MultiDimFit.mH125.root --POI kl --main-label expected --main-color 4 --translate ../../../script/trans.json
mv kl_1Dscan.pdf kl_1Dscan_${version}.pdf
mv kl_1Dscan.png kl_1Dscan_${version}.png

echo "expected CV 1D scan"
combine -M MultiDimFit -t -1 --algo grid --point 45 ${postfitws} --snapshotName MultiDimFit --bypassFrequentistFit --redefineSignalPOIs CV --setParameters r=1,r_gghh=1,r_qqhh=1,kt=1,kl=1,CV=1,C2V=1,mask_SRBin1=0,mask_SRBin2=0,mask_SRBin3=0,mask_fitfail=0,mask_passBin1=1,mask_passBin2=1,mask_passBin3=1,mask_fail=1 --toysFrequentist -m 125 -n CV_scan_${version} --setParameterRanges CV=-2,2 --freezeParameters r,r_gghh,r_qqhh,kt,C2V,kl --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1

python ../../../script/plot1DScan.py higgsCombineCV_scan_${version}.MultiDimFit.mH125.root --POI CV --main-label expected --main-color 4 --translate ../../../script/trans.json
mv CV_1Dscan.pdf CV_1Dscan_${version}.pdf
mv CV_1Dscan.png CV_1Dscan_${version}.png

echo "expected C2V 1D scan"
combine -M MultiDimFit -t -1 --algo grid --point 45 ${postfitws} --snapshotName MultiDimFit --bypassFrequentistFit --redefineSignalPOIs C2V --setParameters r=1,r_gghh=1,r_qqhh=1,kt=1,kl=1,CV=1,C2V=1,mask_SRBin1=0,mask_SRBin2=0,mask_SRBin3=0,mask_fitfail=0,mask_passBin1=1,mask_passBin2=1,mask_passBin3=1,mask_fail=1 --toysFrequentist -m 125 -n C2V_scan_${version} --setParameterRanges C2V=-1,3 --freezeParameters r,r_gghh,r_qqhh,kt,CV,kl --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1

python ../../../script/plot1DScan.py higgsCombineC2V_scan_${version}.MultiDimFit.mH125.root --POI C2V --main-label expected --main-color 4 --translate ../../../script/trans.json
mv C2V_1Dscan.pdf C2V_1Dscan_${version}.pdf
mv C2V_1Dscan.png C2V_1Dscan_${version}.png

#echo "fit mu"
combine -M MultiDimFit -t -1 ${postfitws} --snapshotName MultiDimFit --bypassFrequentistFit --redefineSignalPOIs r --setParameters r=1,r_gghh=1,r_qqhh=1,kt=1,kl=1,CV=1,C2V=1,mask_SRBin1=0,mask_SRBin2=0,mask_SRBin3=0,mask_fitfail=0,mask_SRBin1=1,mask_SRBin2=1,mask_SRBin3=1 --toysFrequentist -m 125 -n mu_testfit_${version} --freezeParameters kl,r_gghh,r_qqhh,kt,CV,C2V --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1

echo "expected mu 1D scan"
combine -M MultiDimFit -t -1 --algo grid --point 13 ${postfitws} --snapshotName MultiDimFit --bypassFrequentistFit --redefineSignalPOIs r --setParameters r=1,r_gghh=1,r_qqhh=1,kt=1,kl=1,CV=1,C2V=1,mask_SRBin1=0,mask_SRBin2=0,mask_SRBin3=0,mask_fitfail=0,mask_passBin1=1,mask_passBin2=1,mask_passBin3=1,mask_fail=1 --toysFrequentist -m 125 -n mu_scan_${version} --setParameterRanges r=-4.5,8.5 --freezeParameters kl,r_gghh,r_qqhh,kt,CV,C2V --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1

python ../../../script/plot1DScan.py higgsCombinemu_scan_${version}.MultiDimFit.mH125.root --POI r --main-label expected --main-color 4 --translate ../../../script/trans.json
mv r_1Dscan.pdf r_1Dscan_${version}.pdf
mv r_1Dscan.png r_1Dscan_${version}.png

#the output of the command above is higgsCombineTest.MultiDimFit.mH125.root, need to upload the snapshot "MultiDimFit" from the bkg-only fit 
#expected limit for SM HH signal strength upper limit:
echo "limit on SM HH xs"
combine -M AsymptoticLimits -m 125 -n Limit_${version} ${postfitws} --snapshotName MultiDimFit --saveWorkspace --saveToys --bypassFrequentistFit --redefineSignalPOIs r --freezeParameters r_gghh,r_qqhh,kt,kl,CV,C2V --setParameters r_gghh=1,r=0,r_qqhh=1,kt=1,kl=1,CV=1,C2V=1,mask_SRBin1=0,mask_SRBin2=0,mask_SRBin3=0,mask_fitfail=0,mask_passBin1=1,mask_passBin2=1,mask_passBin3=1,mask_fail=1 --floatParameters r --toysFrequentist --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --run blind
