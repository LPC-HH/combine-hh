#!/bin/bash
dataset=data_obs
BDTv=$1
echo "BDT version: "$BDTv
ws=HHModel_combined
wsm=${ws}_withmasks
version=$2

combineCards.py fitfail=cards_Bin1/HHModel/fitfail.txt SRBin1=cards_Bin1/HHModel/SRBin1.txt SRBin2=cards_Bin2/HHModel/SRBin2.txt SRBin3=cards_Bin3/HHModel/SRBin3.txt > ${ws}.txt

text2workspace.py -D $dataset ${ws}.txt --channel-masks -o ${wsm}.root

echo "expected limit"
combine -M AsymptoticLimits -m 125 -n ${version} ${wsm}.root --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 

echo "expected limit for BDT Bin 1"
combine -M AsymptoticLimits -m 125 -n ${version}_Bin1 ${wsm}.root --setParameters mask_SRBin1=0,mask_SRBin2=1,mask_SRBin3=1,mask_fitfail=0 --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 

echo "expected limit for BDT Bin 2"
combine -M AsymptoticLimits -m 125 -n ${version}_Bin2 ${wsm}.root --setParameters mask_SRBin1=1,mask_SRBin2=0,mask_SRBin3=1,mask_fitfail=0 --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 

echo "expected limit for BDT Bin 3"
combine -M AsymptoticLimits -m 125 -n ${version}_Bin3 ${wsm}.root --setParameters mask_SRBin1=1,mask_SRBin2=1,mask_SRBin3=0,mask_fitfail=0 --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 

python ../plotting_limit_ch_HH4b.py --inputtag ${version} --unblind True

echo "FitDiagnostic S=0"
combine -M FitDiagnostics ${wsm}.root --setParameters mask_SRBin1=1,mask_SRBin2=1,mask_SRBin3=1,mask_fail=1 --rMin 0 --rMax 4 --saveNormalizations --saveShapes --saveWithUncertainties --saveOverallShapes -n SBplusfail --ignoreCovWarning

echo "expected significance"
combine -M Significance --signif -m 125 -n ${version} ${wsm}.root 
