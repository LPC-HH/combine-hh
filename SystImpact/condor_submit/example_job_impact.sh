#!/bin/sh

#Print out all bash commands
set -x

#Abort bash script on any error
set -e

#Print some basic debugging info
echo "whoami="`whoami`
echo "pwd="`pwd`
echo "hostname="`hostname`
echo "date="`date`
env

#Inside singularity, the scratch directory is here
#This is also where the job starts out
echo "TMP:" `df -h $TMP`
echo "looking inside scratch directory BEFORE job"
ls -al $TMP

np=$1
jobname=$2
ws=$3

read -r workdir < path.txt

cd $workdir

DIRECTORY=${jobname}_${np}
if [ -d "$DIRECTORY" ]; then
  rm -r $DIRECTORY
fi

mkdir ${jobname}_${np}

cd ${jobname}_${np}
#cp ../../../workspace/${ws} .
cp ../higgsCombine_initialFit_${jobname}.MultiDimFit.mH125.root .

export SCRAM_ARCH=slc7_amd64_gcc700
source /cvmfs/cms.cern.ch/cmsset_default.sh
eval `scramv1 runtime -sh`

eval `cmsenv`
env

echo "ROOSYS:" 
echo $ROOTSYS

path=`pwd`

echo $path

echo "input ws:", $ws

#unblinded impact
combineTool.py -M Impacts -m 125 -n $jobname -d ../../../workspace/${ws} --doFits --robustFit 1 --setParameters r=1 --setParameterRanges r=-15,15 --named $np 

#blinded impact
#combineTool.py -M Impacts -t -1 --snapshotName MultiDimFit --bypassFrequentistFit --toysFrequentist -m 125 -n $jobname -d ../../../workspace/${ws} --doFits --robustFit 1 --setParameters mask_SRBin1=0,mask_SRBin2=0,mask_SRBin3=0,mask_fitfail=0,mask_passBin1=1,mask_passBin2=1,mask_passBin3=1,mask_fail=1,r=1 --setParameterRanges r=-15,15 --named $np 
