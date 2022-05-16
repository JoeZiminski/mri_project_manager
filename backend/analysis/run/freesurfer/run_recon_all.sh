#!/bin/bash
#
###################################################################
# Run Freesurfer's recon-all on data stored at $SUBJECT_DIR
# with structural nifti filename $INPUT_FILENAME.
#
# Use recon-all -sd flag to override Freesurfers default behaviour
# to use it's own home dir. For all subjects the $SUBJECT_NAME is
# 'recon_all' as all relevant subject information is held by 
# the $SUBJECT_DIR.
#
# If the folder already exists Freesurfer will run new analysis with
# just the folder path. Cannot input -i if subject folder exists or
# Freesurfer will error.
#
###################################################################

SUBJECT_NAME="recon_all";
SUBJECT_DIR=$1;
INPUT_FILENAME=$2;

if [ ! -d $SUBJECT_DIR"/"$SUBJECT_NAME ]
then
    recon-all -all -s $SUBJECT_NAME -sd $SUBJECT_DIR -i $SUBJECT_DIR"/"$INPUT_FILENAME;
else
    recon-all -all -s $SUBJECT_NAME -sd $SUBJECT_DIR
fi

