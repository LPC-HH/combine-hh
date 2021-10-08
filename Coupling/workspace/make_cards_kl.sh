outdir=cards
if [ ! -d "$outdir" ]; then
  mkdir $outdir
fi

DIRECTORY=${outdir}/${1}${2}_kl
if [ -d "$DIRECTORY" ]; then
  rm -r $DIRECTORY
fi
mkdir $DIRECTORY

inputhist=/storage/af/user/nlu/hh/looper_output/datacard_hist/HHTo4BPlots_Run2_BDT$1.root
cd $DIRECTORY
cp ../../create_datacard_test_kl.py .
cp $inputhist .
python create_datacard_test_kl.py --inputfile HHTo4BPlots_Run2_BDT$1.root

cd ../../
