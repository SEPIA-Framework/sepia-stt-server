#!/bin/bash
if [ -z "$1" ]
  then
    echo "Please add a language code, e.g.: 'de' or 'en'"
    exit
fi
if [ -z "$2" ]
  then
    echo "Please add a number for the new version, e.g.: 09 or 202"
    exit
fi
LANG=$1
VERSION=$2
KALDI_DIR="/opt/kaldi"
KALDI_ADAPT_LM_DIR="/apps/kaldi-adapt-lm"
WORK_DIR="/apps/sepia-stt-server/lm_adapt"
MODEL="$KALDI_DIR/model/kaldi-generic-$LANG-tdnn_sp"
NEW_MODEL="kaldi-generic-$LANG-tdnn_sp_sepia_v$VERSION"
TARGET_DIR="/apps/share/kaldi_models"
SENTENCES_FILE="/apps/share/lm_corpus/sentences_$LANG.txt"
LEXICON_FILE="$MODEL/data/local/dict/lexicon.txt"

echo "---------------------------LM ADAPT ($LANG)-------------------------------"
echo ""
echo "Building new language model ..."
cd "$WORK_DIR"
cp "$SENTENCES_FILE" lm.txt
cut -f 1 -d ' ' "$LEXICON_FILE" >vocab.txt
lmplz -o 4 --prune 0 1 2 3 --limit_vocab_file vocab.txt --interpolate_unigrams 0 <lm.txt >lm.arpa
if [[ $? -ne 0 ]] ; then
    echo build_arpa had an ERROR
    exit 1
fi
echo ""
echo "Adapting model ..."
$KALDI_ADAPT_LM_DIR/kaldi-adapt-lm -f -k $KALDI_DIR $MODEL lm.arpa sepia-$LANG-tdnn_sp
if [[ $? -ne 0 ]] ; then
    echo adapt_lm had an ERROR
    exit 1
fi
echo ""
echo "Moving new model to $TARGET_DIR/$NEW_MODEL"
cd work
tar -xf kaldi-sepia-*.tar.xz
rm kaldi-sepia-*.tar.xz
mv kaldi-sepia-* "$TARGET_DIR/$NEW_MODEL"
if [[ $? -ne 0 ]] ; then
    echo move_model_and_clean had an ERROR
    exit 1
fi
cd ..
rm -r work
rm *.txt
rm *.arpa
echo "Done. Don't forget to set the new model in the STT-server config file"
echo "---------------------------------------------------------------------"
