#!/bin/bash
dataset=data_obs
BDTv=v8p2
ws=HHModel_combined
wsm=${ws}_withmasks
version=Jan27
#mkdir combined_cards
cd combined_cards_${BDTv}
combineCards.py SR_BDT1_fail=cards_Bin1/HHModel/SRfail.txt SR_BDT1_pass=cards_Bin1/HHModel/SRBin1.txt SR_BDT2_pass=cards_Bin2/HHModel/SRBin2.txt SR_BDT3_pass=cards_Bin3/HHModel/SRBin3.txt SB_BDT1_pass=cards_Bin1/HHModel/passBin1.txt SB_BDT2_pass=cards_Bin2/HHModel/passBin2.txt SB_BDT3_pass=cards_Bin3/HHModel/passBin3.txt > ${ws}.txt

#create channel mask so that we can remove SR when fitting to the data to get QCD estimates
text2workspace.py -D $dataset ${ws}.txt --channel-masks -o ${wsm}.root

#text2workspace.py HHModel_combined.txt
echo "bkg-only fit"
combine -D $dataset -M MultiDimFit --saveWorkspace -m 125 ${wsm}.root  --verbose 9 --cminDefaultMinimizerStrategy 1 --setParameters mask_SR_BDT1_pass=1,mask_SR_BDT2_pass=1,mask_SR_BDT3_pass=1,r=0 --freezeParameters r

#combine -M AsymptoticLimits ${wsm}.root -t -1
echo "FitDiagnostic"
combine -M FitDiagnostics ${wsm}.root --plots --setParameters mask_SR_BDT1_pass=1,mask_SR_BDT2_pass=1,mask_SR_BDT3_pass=1 --rMin 0 --rMax 0 --saveNormalizations --saveShapes --saveWithUncertainties --saveOverallShapes --saveNLL -n SBplusfail --ignoreCovWarning

#expected significance
echo "expected significance"
combine -M Significance --signif -m 125 -n ${version} higgsCombineTest.MultiDimFit.mH125.root --snapshotName MultiDimFit -t -1 --expectSignal=1 --saveWorkspace --saveToys --bypassFrequentistFit --setParameters mask_SR_BDT1_pass=0,mask_SR_BDT2_pass=0,mask_SR_BDT3_pass=0,mask_SR_BDT1_fail=0,mask_SB_BDT1_pass=1,mask_SB_BDT2_pass=1,mask_SB_BDT3_pass=1 --floatParameters r --toysFrequentist --verbose 9

#expected limit
#combine -M AsymptoticLimits -D toys/toy_asimov -m 125 -n ${version} higgsCombineJan24.Significance.mH125.123456.root --setParameters mask_SR_BDT1_pass=0,mask_SR_BDT2_pass=0,mask_SR_BDT3_pass=0,mask_SR_BDT1_fail=0,mask_SB_BDT1_pass=1,mask_SB_BDT2_pass=1,mask_SB_BDT3_pass=1,mask_BDT1_fail=1
echo "expected limit"
combine -M AsymptoticLimits -m 125 -n ${version} higgsCombineTest.MultiDimFit.mH125.root --snapshotName MultiDimFit --saveWorkspace --saveToys --bypassFrequentistFit --setParameters mask_SR_BDT1_pass=0,mask_SR_BDT2_pass=0,mask_SR_BDT3_pass=0,mask_SR_BDT1_fail=0,mask_SB_BDT1_pass=1,mask_SB_BDT2_pass=1,mask_SB_BDT3_pass=1 --floatParameters r --toysFrequentist --verbose 9 --run blind

#combine -M AsymptoticLimits higgsCombineTest.MultiDimFit.mH125.root -n ${version} --setParameters mask_SR_BDT1_pass=0,mask_SR_BDT2_pass=0,mask_SR_BDT3_pass=0,mask_SR_BDT1_fail=0,mask_SB_BDT1_pass=1,mask_SB_BDT2_pass=1,mask_SB_BDT3_pass=1,mask_BDT1_fail=1 --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,0:0.1 --run blind --bypassFrequentistFit --toysFrequentist --verbose 9 -t -1 --expectSignal=1 --saveWorkspace --saveToys
#combine -M AsymptoticLimits higgsCombineTest.MultiDimFit.mH125.root -n ${version} --setParameters mask_SR_BDT1_pass=0,mask_SR_BDT2_pass=0,mask_SR_BDT3_pass=0,mask_SR_BDT1_fail=0,mask_SB_BDT1_pass=1,mask_SB_BDT2_pass=1,mask_SB_BDT3_pass=1,mask_BDT1_fail=1 --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,0:0.1 --bypassFrequentistFit --toysFrequentist --verbose 9 
