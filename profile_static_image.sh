#!/bin/bash

# Path to the screenshots folder
screenshots_folder="screenshots"

# Loop through each file in the screenshots folder
for file in "$screenshots_folder"/*; do
    # Check if the file is a regular file
    if [[ -f "$file" ]]; then
        # Run pyinstrument on test_server.py and output the results of the profiling to a file
        pyinstrument -o "$file.txt" test_server.py "$file"
    fi
done