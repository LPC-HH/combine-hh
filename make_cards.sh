DIRECTORY=combined_cards_$1$2
if [ ! -d "$DIRECTORY" ]; then
  mkdir $DIRECTORY
fi

python create_datacard_test.py --carddir $DIRECTORY --inputfile $3/HHTo4BPlots_Run2_BDT$1.root
cd $DIRECTORY

. ../../build_final_test.sh  $1 $2
cd ../../
