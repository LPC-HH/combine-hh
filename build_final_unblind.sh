#!/bin/bash
dataset=data_obs
BDTv=$1
echo "BDT version: "$BDTv
ws=HHModel_combined
version=$2

combineCards.py fitfail=cards_Bin1/HHModel/fitfail.txt SRBin1=cards_Bin1/HHModel/SRBin1.txt SRBin2=cards_Bin2/HHModel/SRBin2.txt SRBin3=cards_Bin3/HHModel/SRBin3.txt > ${ws}.txt
combineCards.py fitfail=cards_Bin1/HHModel/fitfail.txt SRBin1=cards_Bin1/HHModel/SRBin1.txt > ${ws}_Bin1.txt
combineCards.py fitfail=cards_Bin1/HHModel/fitfail.txt SRBin2=cards_Bin2/HHModel/SRBin2.txt > ${ws}_Bin2.txt
combineCards.py fitfail=cards_Bin1/HHModel/fitfail.txt SRBin3=cards_Bin3/HHModel/SRBin3.txt > ${ws}_Bin3.txt

echo "signal_norm_xsbr  group  =  THU_SMHH  pdf_Higgs_ggHH  pdf_Higgs_qqHH  QCDscale_qqHH  BR_hbb" >> ${ws}.txt
echo "signal_norm_xsbr  group  =  THU_SMHH  pdf_Higgs_ggHH  pdf_Higgs_qqHH  QCDscale_qqHH  BR_hbb" >> ${ws}_Bin1.txt
echo "signal_norm_xsbr  group  =  THU_SMHH  pdf_Higgs_ggHH  pdf_Higgs_qqHH  QCDscale_qqHH  BR_hbb" >> ${ws}_Bin2.txt
echo "signal_norm_xsbr  group  =  THU_SMHH  pdf_Higgs_ggHH  pdf_Higgs_qqHH  QCDscale_qqHH  BR_hbb" >> ${ws}_Bin3.txt

echo "signal_norm_xs  group  =  THU_SMHH  pdf_Higgs_ggHH  pdf_Higgs_qqHH  QCDscale_qqHH" >> ${ws}.txt
echo "signal_norm_xs  group  =  THU_SMHH  pdf_Higgs_ggHH  pdf_Higgs_qqHH  QCDscale_qqHH" >> ${ws}_Bin1.txt
echo "signal_norm_xs  group  =  THU_SMHH  pdf_Higgs_ggHH  pdf_Higgs_qqHH  QCDscale_qqHH" >> ${ws}_Bin2.txt
echo "signal_norm_xs  group  =  THU_SMHH  pdf_Higgs_ggHH  pdf_Higgs_qqHH  QCDscale_qqHH" >> ${ws}_Bin3.txt

text2workspace.py -D $dataset ${ws}.txt
text2workspace.py -D $dataset ${ws}_Bin1.txt
text2workspace.py -D $dataset ${ws}_Bin2.txt
text2workspace.py -D $dataset ${ws}_Bin3.txt

echo "observed limit"
combine -M AsymptoticLimits -m 125 -n ${version} ${ws}.root --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 

echo "observed limit for BDT Bin 1"
combine -M AsymptoticLimits -m 125 -n ${version}_Bin1 ${ws}_Bin1.root --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 

echo "observed limit for BDT Bin 2"
combine -M AsymptoticLimits -m 125 -n ${version}_Bin2 ${ws}_Bin2.root  --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 

echo "observed limit for BDT Bin 3"
combine -M AsymptoticLimits -m 125 -n ${version}_Bin3 ${ws}_Bin3.root --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 

python ../plotting_limit_ch_HH4b.py --inputtag ${version} --unblind True

echo "FitDiagnostic S=0"
combine -M FitDiagnostics ${ws}.root --rMin 0 --rMax 4 --saveNormalizations --saveShapes --saveWithUncertainties --saveOverallShapes -n SBplusfail --ignoreCovWarning

cp ${ws}.root morphedWorkspace.root
python ../Coupling/script/importPars.py morphedWorkspace.root fitDiagnosticsSBplusfail.root

echo "observed significance"
combine -M Significance --signif -m 125 -n ${version} ${ws}.root 
