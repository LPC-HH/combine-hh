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
#cp ../../build_final_test_kl.sh .
cp ../../create_datacard_test_kl.py .
cp $inputhist .
python create_datacard_test_kl.py --carddir $1$2 --inputfile HHTo4BPlots_Run2_BDT$1.root

mv cards_Bin1 combined_cards_$1$2/
mv cards_Bin2 combined_cards_$1$2/
mv cards_Bin3 combined_cards_$1$2/ 
cd ../../
