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
pip install --user --upgrade uproot # use uproot4
```

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

The latest input file can be found here: 

```
/eos/cms/store/group/phys_susy/razor/Run2Analysis/HHBoost/hist_for_card/HHTo4BPlots_Run2_BDTv24.root (signal region, v24 BDT)
/eos/cms/store/group/phys_susy/razor/Run2Analysis/HHBoost/hist_for_card/HHTo4BPlots_Run2_BDTv8p2.root (signal region v8p2 BDT)
/eos/cms/store/group/phys_susy/razor/Run2Analysis/HHBoost/hist_for_card/HHTo4BPlots_Run2_ttbarSkim_BDTv24.root  (ttbar CR, v24 BDT)
/eos/cms/store/group/phys_susy/razor/Run2Analysis/HHBoost/hist_for_card/HHTo4BPlots_Run2_ttbarSkim_BDTv8p2.root (ttbar CR, v8p2 BDT)
```

## Checkout this repo and create datacards
```
git clone https://github.com/LPC-HH/combine-hh
cd combine-hh
python create_datacard.py
python create_shapecard.py
```

## Run alphabet cards (final limit cards):
```
./make_cards.sh v8p2yield_AN_sr_sys_0830oldVJetsXS v1
```
Here the first argument should match the input histogram file. 

e.g. here HHTo4BPlots_Run2_BDTv8p2yield_AN_sr_sys_0830oldVJetsXS.root is used, and it is stored in the combine-hh/ directory

The second argument v1 is a version number. in case we want to try different versions using the same HHTo4BPlots_Run2_BDTv8p2yield_AN_sr_sys_0830oldVJetsXS.root file with different systematic uncertainties etc

## Run shape cards:
```
cd cards_shpaes/HHModel
source build.sh
combine -M AsymptoticLimits HHModel_combined.root
combine -M FitDiagnostics HHModel_combined.root --plots --rMin -20 --rMax 20 --saveNormalizations --saveShapes --saveWithUncertainties --saveOverallShapes --saveNLL --ignoreCovWarning
```

## Run F-test (1st vs 2nd order):
change line 193 in create_datacard.py to the bin you want to test (e.g. Bin1)
```
python runFtest.py --v1n1=1 --v1n2=2 --toys=1000 -s 1
```

## produce figure 27 in ANv4

python create_datacard_TTCR.py --inputfile /storage/af/user/nlu/work/HH/CMSSW_9_4_2/src/HHLooper_sysTest/python/HHTo4BPlots_Run2_ttbarSkim_BDTv8p2.root

cd cards_shapes_TTBarCR/HHModel

source build.sh 

combine -M FitDiagnostics HHModel_combined.root --setParameters r=1 --rMin 0 --rMax 2 --skipBOnlyFit --saveNormalizations --saveShapes --saveWithUncertainties --saveOverallShapes -n SBfitonly --ignoreCovWarning

#the output is fitDiagnosticsSBfitonly.root, which will be the input of makePostFitPlot_TTCR.py in the HHLooper directory
