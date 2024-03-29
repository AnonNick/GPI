#!/bin/bash
# The path to the job script
JOB_SCRIPT="gpi_create.pbs"

# Define the path to the log file
LOG_DIR="./logs"
LOG_FILE="cron_submission.log"
mkdir -p "$LOG_DIR"
# Submit the job script to the queue using qsub and capture the output
PBS_OUTPUT=$( /opt/pbs/bin/qsub -q main@desched1 "$JOB_SCRIPT" )

# Extract the PBS job ID from the output
# This assumes the output format is something like "1234.servername"
PBS_JOB_ID=$(echo $PBS_OUTPUT | cut -d'.' -f1)

# Get the current date and time
RUN_DATE=$(date "+%Y-%m-%d %H:%M:%S")
OUT_DATE=$(date "+%Y-%m-%d")
# Append the run date and PBS job ID to the log file
echo -e "[Date: $RUN_DATE] PBS ID: $PBS_JOB_ID, Log File: $OUT_DATE-gpi_create.out" >> "$LOG_DIR/$LOG_FILE"

echo "$PBS_JOB_ID submitted to the queue."
