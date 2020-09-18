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
pip install --user https://github.com/jmduarte/rhalphalib/archive/automcstat.zip
```

## Get input file

## Checkout this repo and create datacards
```
git clone https://github.com/LPC-HH/combine-hh
cd combine-hh
python create_datacard.py
```
