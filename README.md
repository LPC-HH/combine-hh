# combine-hh

## CMSSW+Combine Quickstart
```bash
export SCRAM_ARCH=slc7_amd64_gcc700
cmsrel CMSSW_10_2_13
cd CMSSW_10_2_13/src
cmsenv
git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
cd HiggsAnalysis/CombinedLimit

cd $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit
git fetch origin
git checkout v8.2.0
scramv1 b clean; scramv1 b

cd $CMSSW_BASE/src/
git clone https://github.com/cms-analysis/CombineHarvester.git CombineHarvester
scram b

pip install --user flake8
pip install --user --upgrade numpy
pip install --user https://github.com/jmduarte/rhalphalib/archive/coefsq.zip
pip install --user --upgrade uproot # use uproot4
```

Get the HH model
```bash
wget https://gitlab.cern.ch/hh/tools/inference/-/raw/master/dhi/models/hh_model.py -O $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit/python/hh_model.py
```

For reference, consult
 - https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/
 - https://cms-analysis.github.io/CombineHarvester/

## Get input file

The latest input file for the datacard can be found here: 

```bash
/storage/af/user/nlu/hh/looper_output/datacard_hist/

```

## Checkout this repo and create datacards:
```bash
git clone https://github.com/LPC-HH/combine-hh
cd combine-hh/
./make_cards.sh v8p2yield_AN_sr_sys_0830_fix2017trigSF0913 v1 
```
Here the first argument should match the input histogram file name. 

e.g. here this histogram is used for the preapproval result: 
```bash
/storage/af/user/nlu/hh/looper_output/datacard_hist/HHTo4BPlots_Run2_BDTv8p2yield_AN_sr_sys_0830_fix2017trigSF0913.root
```

The second argument v1 is a version number. in case we want to try different versions using the same input file with different systematic uncertainties etc

## Run F-test (1st vs 2nd order):
For Bin1,
```bash
python runFtest.py --v1n1=1 --v1n2=2 --toys=1000 -s 1 --passBinName Bin1
```

## produce ttbar CR plot figure 27 in ANv4

```bash
python create_datacard_TTCR.py --inputfile /storage/af/user/nlu/work/HH/CMSSW_9_4_2/src/HHLooper_sysTest/python/HHTo4BPlots_Run2_ttbarSkim_BDTv8p2.root
cd cards_shapes_TTBarCR/HHModel
source build.sh 
combine -M FitDiagnostics HHModel_combined.root --setParameters r=1 --rMin 0 --rMax 2 --skipBOnlyFit --saveNormalizations --saveShapes --saveWithUncertainties --saveOverallShapes -n SBfitonly --ignoreCovWarning
```
the output is `fitDiagnosticsSBfitonly.root`, which will be the input of `makePostFitPlot_TTCR.py` in the `HHLooper` directory

## Kl and mu scan

Go to Coupling directory
 
## Systematic uncertainty ranking and impact

Go to SystImpact directory

## Higgs boson self-coupling (kl) and signal strength scan 

Go to Coupling directory

## Upper limit as a function of kl

Go to xsUpperLimit directory

Script not done yet

## Run shape cards:
```
cd cards_shpaes/HHModel
source build.sh
combine -M AsymptoticLimits HHModel_combined.root
combine -M FitDiagnostics HHModel_combined.root --plots --rMin -20 --rMax 20 --saveNormalizations --saveShapes --saveWithUncertainties --saveOverallShapes --saveNLL --ignoreCovWarning
```
