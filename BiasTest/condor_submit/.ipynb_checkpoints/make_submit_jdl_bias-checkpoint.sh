#!/bin/bash
set -e

ws=morphedWorkspacekl.root
ininame=1119v1
rvalue=15
ntoy=2

subdir=submit_${ininame}
if [ -d "$subdir" ]; then
  rm -r $subdir
fi

mkdir $subdir

cd $subdir

cp ../../workspace/$ws .

pwd > path.txt
cp ../example_job_bias.sh .
cp ../example_job_bias.jdl .
cp ../make_submit_jdl_bias.sh .

mkdir logs

RANDOM=$$
itoy=0
while [  $itoy -lt $ntoy ]; do
    iseed=$RANDOM
    echo "itoy and seed:" $itoy $iseed
    name=bias_r${rvalue}_toy${itoy}
    cat example_job_bias.jdl > submit_$name.jdl
    sed -i "s/RVALUE/$rvalue/g" submit_$name.jdl
    sed -i "s/NAME/$name/g" submit_$name.jdl
    sed -i "s/SEED/$iseed/g" submit_$name.jdl
    sed -i "s/WS/$ws/g" submit_$name.jdl
    echo "Queue" >> submit_$name.jdl
    echo >> submit_$name.jdl
    condor_command="condor_submit submit_"$name".jdl"
    echo $condor_command
    condor_submit "submit_"$name".jdl"
    let itoy=itoy+1
done
