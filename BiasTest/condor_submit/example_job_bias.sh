#!/bin/sh

#Print out all bash commands
set -x

#Abort bash script on any error
set -e

env

#Inside singularity, the scratch directory is here
#This is also where the job starts out
echo "TMP:" `df -h $TMP`
echo "looking inside scratch directory BEFORE job"
ls -al $TMP

rv=$1
jobname=$2
seed=$3
ws=$4

read -r workdir < path.txt

cd $workdir

DIRECTORY=${jobname}
if [ ! -d "$DIRECTORY" ]; then
  mkdir ${jobname}
fi

cd ${jobname}

export SCRAM_ARCH=slc7_amd64_gcc700
source /cvmfs/cms.cern.ch/cmsset_default.sh
eval `scramv1 runtime -sh`
eval `cmsenv`
env

path=`pwd`

echo $path

echo "test ws" $ws "with seed" $seed "for toy generation r=" $rv

combine -M GenerateOnly -d ../../../workspace/${ws} --toysFrequentist --bypassFrequentistFit --expectSignal $rv -t 1 --saveToys -s $seed -m 125 -n $jobname

combine -M FitDiagnostics -d ../../../workspace/${ws} --toysFile higgsCombine${jobname}.GenerateOnly.mH125.${seed}.root --rMin -10 --rMax 50 -n $jobname --toysFrequentist -t 1 --ignoreCovWarning

#combine -M FitDiagnostics -d ../../../workspace/${ws} --toysFile higgsCombine${jobname}.GenerateOnly.mH125.${seed}.root --rMin -10 --rMax 50 -n $jobname --toysFrequentist -t 1 --redefineSignalPOIs r --freezeParameters r_gghh,r_qqhh,kt,kl,CV,C2V --floatParameters r --ignoreCovWarning --cminDefaultMinimizerStrategy 1
