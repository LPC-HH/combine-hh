# combine-hh

## CMSSW+Combine Quickstart
```bash
export SCRAM_ARCH=slc7_amd64_gcc700
cmsrel CMSSW_10_2_13
cd CMSSW_10_2_13/src
cmsenv
git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
scram b -j 4
pip install --user flake8
pip install --user --upgrade numpy
pip install --user https://github.com/nsmith-/rhalphalib/archive/master.zip
```

## Get input file

## Checkout this repo and create datacards
```
git clone https://github.com/LPC-HH/combine-hh
cd combine-hh
python create_datacard.py
python create_shapecard.py
```

## Run alphabet cards:
```
cd cards/HHModel
source build.sh
combine -M AsymptoticLimits HHModel_combined.root -t -1
combine -M FitDiagnostics HHModel_combined.root -t -1 --plots --rMin -20 --rMax 20 --setParameters r=1
```


## Run shape cards:
```
cd cards_shpaes/HHModel
source build.sh
combine -M AsymptoticLimits HHModel_combined.root -t -1
combine -M FitDiagnostics HHModel_combined.root -t -1 --plots --rMin -20 --rMax 20 --setParameters r=1
```
