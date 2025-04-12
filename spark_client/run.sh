#!/bin/bash
set -e

# Run your custom script to submit Spark jobs.
echo "Running Spark job submission script..."
bash ./submit_jobs.sh

# Now, execute the original command to start the Jupyter server.
echo "Starting Jupyter server..."
exec jupyter lab --ip=0.0.0.0 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''

