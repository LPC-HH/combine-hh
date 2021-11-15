DIRECTORY=combined_cards_$1$2
if [ ! -d "$DIRECTORY" ]; then
  mkdir $DIRECTORY
fi

if [ $4 == True ]
then
    python create_datacard_test.py --carddir $DIRECTORY --inputfile $3/HHTo4BPlots_Run2_BDT$1.root --add-blinded $4
else
    python create_datacard_test.py --carddir $DIRECTORY --inputfile $3/HHTo4BPlots_Run2_BDT$1.root
fi
cd $DIRECTORY

if [ $4 == True ]
then
  echo "blinded fit"
  . ../build_final_test.sh  $1 $2
else
  echo "unblinded fit"
  . ../build_final_unblind.sh  $1 $2 
fi
cd ../
