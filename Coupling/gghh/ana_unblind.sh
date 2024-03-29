#!/bin/bash
dataset=data_obs
version=$1
inputdir=$2
ws=HHModel_combined_${version}

echo "combine cards"
combineCards.py fitfail=cards_Bin1/HHModel/fitfail.txt SRBin1=cards_Bin1/HHModel/SRBin1.txt SRBin2=cards_Bin2/HHModel/SRBin2.txt SRBin3=cards_Bin3/HHModel/SRBin3.txt > ${ws}.txt
combineCards.py fitfail=cards_Bin1/HHModel/fitfail.txt SRBin1=cards_Bin1/HHModel/SRBin1.txt > ${ws}_bin1.txt
combineCards.py fitfail=cards_Bin1/HHModel/fitfail.txt SRBin2=cards_Bin2/HHModel/SRBin2.txt > ${ws}_bin2.txt
combineCards.py fitfail=cards_Bin1/HHModel/fitfail.txt SRBin3=cards_Bin3/HHModel/SRBin3.txt > ${ws}_bin3.txt

echo "build the ws"
text2workspace.py ${ws}.txt -P HiggsAnalysis.CombinedLimit.hh_model:model_default --mass=125 --channel-masks
text2workspace.py ${ws}_bin1.txt -P HiggsAnalysis.CombinedLimit.hh_model:model_default --mass=125 --channel-masks
text2workspace.py ${ws}_bin2.txt -P HiggsAnalysis.CombinedLimit.hh_model:model_default --mass=125 --channel-masks
text2workspace.py ${ws}_bin3.txt -P HiggsAnalysis.CombinedLimit.hh_model:model_default --mass=125 --channel-masks

#echo "prepare datacard for HH combination"
# https://cms-b2g.docs.cern.ch/combine/StatTests/
# https://twiki.cern.ch/twiki/bin/view/CMS/SWGuideHiggsAnalysisCombinedLimit
# https://twiki.cern.ch/twiki/bin/view/CMS/HiggsWG/HiggsPAGPreapprovalChecks

echo "fit kl"
combine -M MultiDimFit ${ws}.root --redefineSignalPOIs kl -m 125 -n kl_bestfit_${version} --freezeParameters r,r_gghh,r_qqhh,kt,CV,C2V --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1

echo "observed kl 1D scan"
combine -M MultiDimFit --algo grid --point 45 ${ws}.root --redefineSignalPOIs kl -m 125 -n kl_scan_${version} --setParameterRanges kl=-18.5,26.5 --freezeParameters r,r_gghh,r_qqhh,kt,CV,C2V --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1

echo "expected kl 1D scan"
combine -M MultiDimFit -t -1 --algo grid --point 45 ${ws}.root --redefineSignalPOIs kl -m 125 -n kl_exp_scan_${version} --setParameterRanges kl=-18.5,26.5 --freezeParameters r,r_gghh,r_qqhh,kt,CV,C2V --toysFrequentist --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1

python ../../../script/plot1DScan.py higgsCombinekl_scan_${version}.MultiDimFit.mH125.root --POI kl --main-label observed --main-color 1 --translate ../../../script/trans.json --others higgsCombinekl_exp_scan_${version}.MultiDimFit.mH125.root:expected:4:1
mv kl_1Dscan.pdf kl_1Dscan_${version}.pdf
mv kl_1Dscan.png kl_1Dscan_${version}.png
mv output.txt output_kl_1Dscan_${version}.txt

echo "fit mu"
combine -M MultiDimFit ${ws}.root --redefineSignalPOIs r -m 125 -n mu_testfit_${version} --freezeParameters kl,r_gghh,r_qqhh,kt,CV,C2V --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1

echo "observed mu 1D scan"
combine -M MultiDimFit --algo grid --point 17 ${ws}.root --redefineSignalPOIs r -m 125 -n mu_scan_${version} --setParameterRanges r=-4.5,12.5 --freezeParameters kl,r_gghh,r_qqhh,kt,CV,C2V --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1
combine -M MultiDimFit --algo grid --point 17 ${ws}.root --redefineSignalPOIs r -m 125 -n mu_Bin1_scan_${version} --setParameters mask_SRBin1=0,mask_SRBin2=1,mask_SRBin3=1 --setParameterRanges r=-4.5,12.5 --freezeParameters kl,r_gghh,r_qqhh,kt,CV,C2V --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1
combine -M MultiDimFit --algo grid --point 17 ${ws}.root --redefineSignalPOIs r -m 125 -n mu_Bin2_scan_${version} --setParameters mask_SRBin1=1,mask_SRBin2=0,mask_SRBin3=1 --setParameterRanges r=-4.5,29.5 --freezeParameters kl,r_gghh,r_qqhh,kt,CV,C2V --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1
combine -M MultiDimFit --algo grid --point 20 ${ws}.root --redefineSignalPOIs r -m 125 -n mu_Bin3_scan_${version} --setParameters mask_SRBin1=1,mask_SRBin2=1,mask_SRBin3=0 --setParameterRanges r=-20,30 --freezeParameters kl,r_gghh,r_qqhh,kt,CV,C2V --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1

echo "expected mu 1D scan"
combine -M MultiDimFit -t -1 --algo grid --point 20 ${ws}.root --redefineSignalPOIs r -m 125 -n mu_exp_scan_${version}  --setParameters r=1,r_gghh=1,r_qqhh=1,kt=1,kl=1,CV=1,C2V=1 --setParameterRanges r=-5,5 --freezeParameters kl,r_gghh,r_qqhh,kt,CV,C2V --toysFrequentist --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1
combine -M MultiDimFit -t -1 --algo grid --point 20 ${ws}_bin1.root --redefineSignalPOIs r -m 125 -n mu_exp_Bin1_scan_${version} --setParameters r=1,r_gghh=1,r_qqhh=1,kt=1,kl=1,CV=1,C2V=1 --setParameterRanges r=-5,5 --freezeParameters kl,r_gghh,r_qqhh,kt,CV,C2V --toysFrequentist --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1
combine -M MultiDimFit -t -1 --algo grid --point 20 ${ws}_bin2.root --redefineSignalPOIs r -m 125 -n mu_exp_Bin2_scan_${version} --setParameters r=1,r_gghh=1,r_qqhh=1,kt=1,kl=1,CV=1,C2V=1 --setParameterRanges r=-10,10 --freezeParameters kl,r_gghh,r_qqhh,kt,CV,C2V --toysFrequentist --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1
combine -M MultiDimFit -t -1 --algo grid --point 20 ${ws}_bin3.root --redefineSignalPOIs r -m 125 -n mu_exp_Bin3_scan_${version} --setParameters r=1,r_gghh=1,r_qqhh=1,kt=1,kl=1,CV=1,C2V=1 --setParameterRanges r=-20,20 --freezeParameters kl,r_gghh,r_qqhh,kt,CV,C2V --toysFrequentist --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1

python ../../../script/plot1DScan.py higgsCombinemu_scan_${version}.MultiDimFit.mH125.root --POI r --main-label expected --main-color 1 --translate ../../../script/trans.json
mv r_1Dscan.pdf r_1Dscan_${version}.pdf
mv r_1Dscan.png r_1Dscan_${version}.png
mv output.txt r_1Dscan_${version}.txt

python ../../../script/plot1DScan.py higgsCombinemu_scan_${version}.MultiDimFit.mH125.root --POI r --main-label combined_observed --main-color 1 --translate ../../../script/trans.json --others higgsCombinemu_Bin1_scan_${version}.MultiDimFit.mH125.root:Bin1_observed:4:1 higgsCombinemu_Bin2_scan_${version}.MultiDimFit.mH125.root:Bin2_observed:2:1 higgsCombinemu_Bin3_scan_${version}.MultiDimFit.mH125.root:Bin3_observed:3:1 higgsCombinemu_exp_scan_${version}.MultiDimFit.mH125.root:Combined_expected:1:2 higgsCombinemu_exp_Bin1_scan_${version}.MultiDimFit.mH125.root:Bin1_expected:4:2 higgsCombinemu_exp_Bin2_scan_${version}.MultiDimFit.mH125.root:Bin2_expected:2:2 higgsCombinemu_exp_Bin3_scan_${version}.MultiDimFit.mH125.root:Bin3_expected:3:2  --y-max 14 --y-min 0 --y-cut 14
mv r_1Dscan.pdf r_1Dscan_categories_${version}.pdf
mv r_1Dscan.png r_1Dscan_categories_${version}.png
mv output.txt r_1Dscan_categories_${version}.txt

echo "FitDiagnostic S+B fit and b-only fit"
combine -M FitDiagnostics ${ws}.root --rMin 0 --rMax 10 --redefineSignalPOIs r --freezeParameters r_gghh,r_qqhh,kt,kl,CV,C2V --floatParameters r --saveNormalizations --saveShapes --saveWithUncertainties --saveOverallShapes -n SBplusfail --ignoreCovWarning

echo "observed significance"
combine -M Significance --signif -m 125 -n ${version} ${ws}.root --redefineSignalPOIs r --freezeParameters r_gghh,r_qqhh,kt,kl,CV,C2V --floatParameters r 

echo "observed CV 1D scan"
combine -M MultiDimFit --algo grid --point 45 ${ws}.root --redefineSignalPOIs CV -m 125 -n CV_scan_${version} --setParameterRanges CV=-2,2 --freezeParameters r,r_gghh,r_qqhh,kt,C2V,kl --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1

echo "expected CV 1D scan"
combine -M MultiDimFit -t -1 --algo grid --point 45 ${ws}.root --redefineSignalPOIs CV -m 125 -n CV_exp_scan_${version} --setParameterRanges CV=-2,2 --freezeParameters r,r_gghh,r_qqhh,kt,C2V,kl --toysFrequentist --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1

python ../../../script/plot1DScan.py higgsCombineCV_scan_${version}.MultiDimFit.mH125.root --POI CV --main-label observed --main-color 1 --translate ../../../script/trans.json --others higgsCombineCV_exp_scan_${version}.MultiDimFit.mH125.root:expected:4:1
mv CV_1Dscan.pdf CV_1Dscan_${version}.pdf
mv CV_1Dscan.png CV_1Dscan_${version}.png
mv output.txt output_CV_1Dscan_${version}.txt

echo "observed C2V 1D scan"
combine -M MultiDimFit --algo grid --point 45 ${ws}.root --redefineSignalPOIs C2V -m 125 -n C2V_scan_${version} --setParameterRanges C2V=-1,3 --freezeParameters r,r_gghh,r_qqhh,kt,CV,kl --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1

echo "expected C2V 1D scan"
combine -M MultiDimFit -t -1 --algo grid --point 45 ${ws}.root --redefineSignalPOIs C2V -m 125 -n C2V_exp_scan_${version} --setParameterRanges C2V=-1,3 --freezeParameters r,r_gghh,r_qqhh,kt,CV,kl --toysFrequentist --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1

python ../../../script/plot1DScan.py higgsCombineC2V_scan_${version}.MultiDimFit.mH125.root --POI C2V --main-label observed --main-color 1 --translate ../../../script/trans.json --others higgsCombineC2V_exp_scan_${version}.MultiDimFit.mH125.root:expected:4:1
mv C2V_1Dscan.pdf C2V_1Dscan_${version}.pdf
mv C2V_1Dscan.png C2V_1Dscan_${version}.png
mv output.txt C2V_1Dscan_${version}.txt

echo "limit on SM HH xs"
combine -M AsymptoticLimits -m 125 -n Limit_${version} ${ws}.root --redefineSignalPOIs r --freezeParameters r_gghh,r_qqhh,kt,kl,CV,C2V --floatParameters r --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1
combine -M AsymptoticLimits -m 125 -n Limit_Bin1_${version} --setParameters mask_SRBin1=0,mask_SRBin2=1,mask_SRBin3=1 ${ws}.root --redefineSignalPOIs r --freezeParameters r_gghh,r_qqhh,kt,kl,CV,C2V --floatParameters r --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1
combine -M AsymptoticLimits -m 125 -n Limit_Bin2_${version} --setParameters mask_SRBin1=1,mask_SRBin2=0,mask_SRBin3=1 ${ws}.root --redefineSignalPOIs r --freezeParameters r_gghh,r_qqhh,kt,kl,CV,C2V --floatParameters r --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1
combine -M AsymptoticLimits -m 125 -n Limit_Bin3_${version} --setParameters mask_SRBin1=1,mask_SRBin2=1,mask_SRBin3=0 ${ws}.root --redefineSignalPOIs r --freezeParameters r_gghh,r_qqhh,kt,kl,CV,C2V --floatParameters r --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1
