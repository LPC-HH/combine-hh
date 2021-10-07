version=$1

subdir=result_${version}
if [ -d "$subdir" ]; then
  rm -r $subdir
fi
mkdir $subdir
cd $subdir

cp ../../condor_submit/submit_${version}/${version}_*/*higgsCombine_paramFit_${version}* .
cp ../../condor_submit/submit_${version}/higgsCombine_initialFit_${version}.MultiDimFit.mH125.root .

combineTool.py -M Impacts -d higgsCombine_initialFit_${version}.MultiDimFit.mH125.root -m 125 -o impacts_${version}.json -n ${version}

plotImpacts.py -i impacts_${version}.json -t ../trans.json -o impacts

mv impacts.pdf impacts_${version}.pdf
