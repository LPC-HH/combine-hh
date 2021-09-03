#!/bin/bash
dataset=data_obs
BDTv=$1
echo "BDT version: "$BDTv
ws=HHModel_combined
wsm=${ws}_withmasks
version=$2
cd combined_cards_${BDTv}${version}
combineCards.py fitfail=cards_Bin1/HHModel/fitfail.txt fail=cards_Bin1/HHModel/fail.txt SRBin1=cards_Bin1/HHModel/SRBin1.txt SRBin2=cards_Bin2/HHModel/SRBin2.txt SRBin3=cards_Bin3/HHModel/SRBin3.txt passBin1=cards_Bin1/HHModel/passBin1.txt passBin2=cards_Bin2/HHModel/passBin2.txt passBin3=cards_Bin3/HHModel/passBin3.txt > ${ws}.txt

#create channel mask so that we can remove SR when fitting to the data to get QCD estimates
text2workspace.py -D $dataset ${ws}.txt --channel-masks -o ${wsm}.root

#text2workspace.py HHModel_combined.txt
echo "bkg-only fit"
combine -D $dataset -M MultiDimFit --saveWorkspace -m 125 ${wsm}.root  --verbose 9 --cminDefaultMinimizerStrategy 1 --setParameters mask_SRBin1=1,mask_SRBin2=1,mask_SRBin3=1,mask_fail=1,r=0 --freezeParameters r 

echo "expected limit"
combine -M AsymptoticLimits -m 125 -n ${version} higgsCombineTest.MultiDimFit.mH125.root --snapshotName MultiDimFit --saveWorkspace --saveToys --bypassFrequentistFit --setParameters mask_SRBin1=0,mask_SRBin2=0,mask_SRBin3=0,mask_fitfail=0,mask_passBin1=1,mask_passBin2=1,mask_passBin3=1,mask_fail=1 --floatParameters r --toysFrequentist --verbose 9 --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --run blind

echo "expected limit for BDT Bin 1"
combine -M AsymptoticLimits -m 125 -n ${version}_Bin1 higgsCombineTest.MultiDimFit.mH125.root --snapshotName MultiDimFit --saveWorkspace --saveToys --bypassFrequentistFit --setParameters mask_SRBin1=0,mask_SRBin2=1,mask_SRBin3=1,mask_fitfail=0,mask_passBin1=1,mask_passBin2=1,mask_passBin3=1,mask_fail=1 --floatParameters r --toysFrequentist --verbose 9 --run blind

echo "expected limit for BDT Bin 2"
combine -M AsymptoticLimits -m 125 -n ${version}_Bin2 higgsCombineTest.MultiDimFit.mH125.root --snapshotName MultiDimFit --saveWorkspace --saveToys --bypassFrequentistFit --setParameters mask_SRBin1=1,mask_SRBin2=0,mask_SRBin3=1,mask_fitfail=0,mask_passBin1=1,mask_passBin2=1,mask_passBin3=1,mask_fail=1 --floatParameters r --toysFrequentist --verbose 9 --run blind

echo "expected limit for BDT Bin 3"
combine -M AsymptoticLimits -m 125 -n ${version}_Bin3 higgsCombineTest.MultiDimFit.mH125.root --snapshotName MultiDimFit --saveWorkspace --saveToys --bypassFrequentistFit --setParameters mask_SRBin1=1,mask_SRBin2=1,mask_SRBin3=0,mask_fitfail=0,mask_passBin1=1,mask_passBin2=1,mask_passBin3=1,mask_fail=1 --floatParameters r --toysFrequentist --verbose 9 --run blind

echo "FitDiagnostic S=0"
combine -M FitDiagnostics ${wsm}.root --setParameters mask_SRBin1=1,mask_SRBin2=1,mask_SRBin3=1,mask_fail=1 --rMin 0 --rMax 2 --saveNormalizations --saveShapes --saveWithUncertainties --saveOverallShapes -n SBplusfail --ignoreCovWarning

echo "FitDiagnostic S=1"
combine -M FitDiagnostics ${wsm}.root --setParameters mask_SRBin1=1,mask_SRBin2=1,mask_SRBin3=1,mask_fail=1 --rMin 1 --rMax 1 --skipBOnlyFit --saveNormalizations --saveShapes --saveWithUncertainties --saveOverallShapes -n SBplusfailSfit --ignoreCovWarning

echo "expected significance"
combine -M Significance --signif -m 125 -n ${version} higgsCombineTest.MultiDimFit.mH125.root --snapshotName MultiDimFit -t -1 --expectSignal=1 --saveWorkspace --saveToys --bypassFrequentistFit --setParameters mask_SRBin1=0,mask_SRBin2=0,mask_SRBin3=0,mask_fitfail=0,mask_passBin1=1,mask_passBin2=1,mask_passBin3=1,mask_fail=1 --floatParameters r --toysFrequentist
