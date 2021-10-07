1.

put the name of the ws in make_submit_jdl_label_MC.sh
./make_submit_jdl_label_MC.sh

2.

#this is initial fit, only need to do it once
combineTool.py -M Impacts -t -1 --snapshotName MultiDimFit --bypassFrequentistFit --toysFrequentist -m 125 -n ${ininame} -d ${ws} --doInitialFit --robustFit 1 --setParameters mask_SRBin1=0,mask_SRBin2=0,mask_SRBin3=0,mask_fitfail=0,mask_passBin1=1,mask_passBin2=1,mask_passBin3=1,mask_fail=1,r=1 --setParameterRanges r=-10,10 --cminDefaultMinimizerStrategy=1 --saveWorkspace

3.
line 33 of make_submit_jdl_impact.sh 

list of nuisance parameters to study:

nuisance parameter with a constraint term: np_con.txt

free nuisance parameter: np_uncons.txt 
