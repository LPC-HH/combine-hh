#!/bin/bash
#instructions: https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/part3/nonstandard/
#higgsCombineTest.MultiDimFit.mH125.root needs to be in workspace/ directory
set -e

ws=HHModel_combined_1123v1.root
#blinded workspace with snapshot of bkg-ony fit: higgsCombineTest.MultiDimFit.mH125.0913.root
ininame=1123v1

subdir=submit_${ininame}
if [ -d "$subdir" ]; then
  rm -r $subdir
fi
mkdir $subdir
mkdir logs

cd $subdir

cp ../../workspace/$ws .

pwd > path.txt
cp ../example_job_impact.sh .
cp ../example_job_impact.jdl .
cp ../make_submit_jdl_impact.sh .

#this is initial fit, only need to do it once
#unblinded case
combineTool.py -M Impacts -m 125 -n ${ininame} -d ${ws} --doInitialFit --robustFit 1 --setParameters r=1 --setParameterRanges r=-15,15 --cminDefaultMinimizerStrategy=1 --saveWorkspace
#blinded case
#combineTool.py -M Impacts -t -1 --snapshotName MultiDimFit --bypassFrequentistFit --toysFrequentist -m 125 -n ${ininame} -d ${ws} --doInitialFit --robustFit 1 --setParameters mask_SRBin1=0,mask_SRBin2=0,mask_SRBin3=0,mask_fitfail=0,mask_passBin1=1,mask_passBin2=1,mask_passBin3=1,mask_fail=1,r=1 --setParameterRanges r=-10,10 --cminDefaultMinimizerStrategy=1 --saveWorkspace

#check suggested by Javier for blinded workspace
#combineTool.py -M Impacts -t -1 --toysFrequentist -m 125 -n ${ininame} -d ${ws} --doInitialFit --robustFit 1 --setParameters mask_SRBin1=1,mask_SRBin2=1,mask_SRBin3=1,mask_fitfail=0,mask_passBin1=0,mask_passBin2=0,mask_passBin3=0,mask_fail=1,r=1 --setParameterRanges r=-10,10 --cminDefaultMinimizerStrategy=1 --saveWorkspace

for nps in `cat ../np_uncons.txt`; do
    echo "test nuisance parameter:", $nps
    while IFS=',' read -ra ADDR; do
      for inp in "${ADDR[@]}"; do
        echo "$inp"
        name=${inp}_${ininame}
        cat example_job_impact.jdl > submit_$name.jdl
        sed -i "s/NAME/$ininame/g" submit_$name.jdl
        sed -i "s/NP/$inp/g" submit_$name.jdl
        sed -i "s/WS/$ws/g" submit_$name.jdl
        echo "Queue" >> submit_$name.jdl
        echo >> submit_$name.jdl
        condor_command="condor_submit submit_"$name".jdl"
        echo $condor_command
        condor_submit "submit_"$name".jdl"
      done
    done  <<< "$nps"
done
