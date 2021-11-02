#!/bin/bash
dataset=data_obs
version=$1
inputdir=$2
vbfmode=$3 # 0=ggf, 1=vbf, 2=ggf+vbf
ws=HHModel_combined_${version}

if [ $vbfmode -eq 2 ]; then
    combineCards.py fitfail=cards_Bin1/HHModel/fitfail.txt fail=cards_Bin1/HHModel/fail.txt SRBin1=cards_Bin1/HHModel/SRBin1.txt SRBin2=cards_Bin2/HHModel/SRBin2.txt SRBin3=cards_Bin3/HHModel/SRBin3.txt passBin1=cards_Bin1/HHModel/passBin1.txt passBin2=cards_Bin2/HHModel/passBin2.txt passBin3=cards_Bin3/HHModel/passBin3.txt vbf=${inputdir}/vbf_datacard.txt > ${ws}.txt
elif [ $vbfmode -eq 1 ]; then
    combineCards.py vbf=${inputdir}/vbf_datacard.txt > ${ws}.txt
else
    combineCards.py fitfail=cards_Bin1/HHModel/fitfail.txt fail=cards_Bin1/HHModel/fail.txt SRBin1=cards_Bin1/HHModel/SRBin1.txt SRBin2=cards_Bin2/HHModel/SRBin2.txt SRBin3=cards_Bin3/HHModel/SRBin3.txt passBin1=cards_Bin1/HHModel/passBin1.txt passBin2=cards_Bin2/HHModel/passBin2.txt passBin3=cards_Bin3/HHModel/passBin3.txt > ${ws}.txt
fi

echo "build the ws"
if [ $vbfmode -gt 0 ]
then
    text2workspace.py ${ws}.txt -P HiggsAnalysis.CombinedLimit.hh_model:model_all --channel-masks --mass=125
else
    text2workspace.py ${ws}.txt -P HiggsAnalysis.CombinedLimit.hh_model:model_default --channel-masks --mass=125
fi

#echo "prepare datacard for HH combination"
# https://cms-b2g.docs.cern.ch/combine/StatTests/
# https://twiki.cern.ch/twiki/bin/view/CMS/SWGuideHiggsAnalysisCombinedLimit
# https://twiki.cern.ch/twiki/bin/view/CMS/HiggsWG/HiggsPAGPreapprovalChecks

#echo "fit kl"
#combine -M MultiDimFit ${ws}.root --redefineSignalPOIs kl -m 125 -n kl_bestfit_${version} --freezeParameters r,r_gghh,r_qqhh,kt,CV,C2V --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1

echo "expected kl 1D scan"
combine -M MultiDimFit -t -1 --algo grid --point 45 ${ws}.root --redefineSignalPOIs kl -m 125 -n kl_scan_${version} --setParameterRanges kl=-18.5,26.5 --freezeParameters r,r_gghh,r_qqhh,kt,CV,C2V --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1

python ../../../../script/plot1DScan.py higgsCombinekl_scan_${version}.MultiDimFit.mH125.root --POI kl --main-label expected --main-color 4 --translate ../../../../script/trans.json
mv kl_1Dscan.pdf kl_1Dscan_${version}.pdf
mv kl_1Dscan.png kl_1Dscan_${version}.png

echo "expected CV 1D scan"
combine -M MultiDimFit -t -1 --algo grid --point 45 ${ws}.root --redefineSignalPOIs CV -m 125 -n CV_scan_${version} --setParameterRanges CV=-2,2 --freezeParameters r,r_gghh,r_qqhh,kt,C2V,kl --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1

python ../../../../script/plot1DScan.py higgsCombineCV_scan_${version}.MultiDimFit.mH125.root --POI CV --main-label expected --main-color 4 --translate ../../../../script/trans.json
mv CV_1Dscan.pdf CV_1Dscan_${version}.pdf
mv CV_1Dscan.png CV_1Dscan_${version}.png

echo "expected C2V 1D scan"
combine -M MultiDimFit -t -1 --algo grid --point 45 ${ws}.root --redefineSignalPOIs C2V -m 125 -n C2V_scan_${version} --setParameterRanges C2V=-1,3 --freezeParameters r,r_gghh,r_qqhh,kt,CV,kl --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1

python ../../../../script/plot1DScan.py higgsCombineC2V_scan_${version}.MultiDimFit.mH125.root --POI C2V --main-label expected --main-color 4 --translate ../../../../script/trans.json
mv C2V_1Dscan.pdf C2V_1Dscan_${version}.pdf
mv C2V_1Dscan.png C2V_1Dscan_${version}.png

#echo "fit mu"
#combine -M MultiDimFit -t -1 ${ws}.root --redefineSignalPOIs r -m 125 -n mu_testfit_${version} --freezeParameters kl,r_gghh,r_qqhh,kt,CV,C2V --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1

echo "expected mu 1D scan"
combine -M MultiDimFit --algo grid --point 13 ${ws}.root --redefineSignalPOIs r -m 125 -n mu_scan_${version} --setParameterRanges r=-4.5,8.5 --freezeParameters kl,r_gghh,r_qqhh,kt,CV,C2V --saveNLL --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1

python ../../../../script/plot1DScan.py higgsCombinemu_scan_${version}.MultiDimFit.mH125.root --POI r --main-label expected --main-color 4 --translate ../../../../script/trans.json
mv r_1Dscan.pdf r_1Dscan_${version}.pdf
mv r_1Dscan.png r_1Dscan_${version}.png

#echo "limit on SM HH xs"
#combine -M AsymptoticLimits -m 125 -n Limit_${version} ${ws}.root --redefineSignalPOIs r --freezeParameters r_gghh,r_qqhh,kt,kl,CV,C2V --floatParameters r --cminDefaultMinimizerStrategy 1 --cminFallbackAlgo Minuit2,Migrad,1:0.1 --verbose -1
