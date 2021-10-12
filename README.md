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
pip install --user https://github.com/nsmith-/rhalphalib/archive/master.zip
pip install --user --upgrade uproot # use uproot4
```
Get the HH model

```
https://gitlab.cern.ch/hh/tools/inference/-/blob/master/dhi/models/hh_model.py
```
put this file in the folder:

```
/CMSSW_10_2_13/src/HiggsAnalysis/CombinedLimit/python/
```
ref:

https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/

https://cms-analysis.github.io/CombineHarvester/

## the packakge will be installed in here on Caltech T2
/storage/af/user/$USER/.local/lib/python2.7/site-packages/rhalphalib

in function.py: use coef*coef instead of coef for the BernsteinPoly function to avoid negative PDF

```     
        # Construct parameter tensor
        import ROOT
        self._params = np.full(self._shape, None)
        for ipar, initial in np.ndenumerate(self._init_params):
            param = IndependentParameter('_'.join([self.name] + ['%s_par%d' % (d, i) for d, i in zip(self._dim_names, ipar)]), initial, lo=limits[0], hi=limits[1])
            paramsq = DependentParameter('_'.join([self.name] + ['%s_parsq%d' % (d, i) for d, i in zip(self._dim_names, ipar)]), "{0}*{0}", param)
            self._params[ipar] = paramsq

```
e.g: /storage/af/user/nlu/.local/lib/python2.7/site-packages/rhalphalib/function.py


## Get input file

The latest input file for the datacard can be found here: 

```
/storage/af/user/nlu/hh/looper_output/datacard_hist/

```

## Checkout this repo and create datacards:
```
git clone https://github.com/LPC-HH/combine-hh
cd combine-hh/
./make_cards.sh v8p2yield_AN_sr_sys_0830_fix2017trigSF0913 v1 
```
Here the first argument should match the input histogram file name. 

e.g. here this histogram is used for the preapproval result: /storage/af/user/nlu/Hmm/Combined_v8.1.0/CMSSW_10_2_13/src/HiggsAnalysis/HH4b/HHTo4BPlots_Run2_BDTv8p2yield_AN_sr_sys_0830_fix2017trigSF0913.root

The second argument v1 is a version number. in case we want to try different versions using the same input file with different systematic uncertainties etc

## Run F-test (1st vs 2nd order):
change line 193 in create_datacard.py to the bin you want to test (e.g. Bin1)
```
python runFtest.py --v1n1=1 --v1n2=2 --toys=1000 -s 1
```

## produce limit plot in the three categories separately and combined

python plotting_limit_ch_HH4b.py

change the output of the limits here:
https://github.com/LPC-HH/combine-hh/blob/3557875a8ef493935b83ab2c67f6051bb26bd4ca/plotting_limit_ch_HH4b.py#L115-L118

## produce ttbar CR plot figure 27 in ANv4

python create_datacard_TTCR.py --inputfile /storage/af/user/nlu/work/HH/CMSSW_9_4_2/src/HHLooper_sysTest/python/HHTo4BPlots_Run2_ttbarSkim_BDTv8p2.root

cd cards_shapes_TTBarCR/HHModel

source build.sh 

combine -M FitDiagnostics HHModel_combined.root --setParameters r=1 --rMin 0 --rMax 2 --skipBOnlyFit --saveNormalizations --saveShapes --saveWithUncertainties --saveOverallShapes -n SBfitonly --ignoreCovWarning

#the output is fitDiagnosticsSBfitonly.root, which will be the input of makePostFitPlot_TTCR.py in the HHLooper directory

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

