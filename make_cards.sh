python create_datacard_test.py --carddir $1$2 --inputfile HHTo4BPlots_Run2_BDT$1.root
cd cards/$1$2
cp ../../build_final_test.sh .
cp ../../HHTo4BPlots_Run2_BDT$1.root .
cp ../../create_datacard_test.py .

DIRECTORY=combined_cards_$1$2
if [ ! -d "$DIRECTORY" ]; then
  mkdir $DIRECTORY
fi

mkdir $DIRECTORY

mv cards_Bin1 combined_cards_$1$2/
mv cards_Bin2 combined_cards_$1$2/
mv cards_Bin3 combined_cards_$1$2/ 
./build_final_test.sh  $1 $2
cd ../../
