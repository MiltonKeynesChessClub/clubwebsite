#!/bin/bash

# Script to import internal competition results from Google spreadsheets
# Filters for active competitions that have Google sheet URLs and downloads them

set -e  # Exit on any error

# Configuration
YAML_FILE="../../_data/mkchessclub.yml"
OUTPUT_DIR="../../_data/results/internal"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to script directory
cd "$SCRIPT_DIR"

# Check if curl is installed
if ! command -v curl &> /dev/null; then
    echo "Error: curl is not installed."
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

echo "Importing internal competition results..."

# Parse the YAML file to find active competitions with Google sheets
# This approach uses awk to parse the YAML structure
awk '
/^  internal:/ { in_internal = 1; next }
/^  [a-z]/ && in_internal { in_internal = 0 }
in_internal && /^  - season:/ {
    season = $3
    active = ""
    googlesheet = ""
    next
}
in_internal && /^    active:/ { active = $2; next }
in_internal && /^    googlesheet:/ {
    googlesheet = $2
    if (active == "true" && googlesheet != "") {
        print season "|" googlesheet
    }
    next
}
' "$YAML_FILE" | while IFS='|' read -r season url; do
    # Skip empty lines
    if [[ -z "$season" || -z "$url" ]]; then
        continue
    fi

    echo "Processing season $season..."
    echo "  URL: $url"

    # Create season directory if it doesn't exist
    season_dir="$OUTPUT_DIR/$season"
    mkdir -p "$season_dir"

    # Download the CSV file
    output_file="$season_dir/competition_data.csv"
    rm -f "$output_file"

    if curl -s -L -o "$output_file" "$url"; then
        echo "  ✓ Downloaded to: $output_file"

        # Check if the file has content
        if [[ -s "$output_file" ]]; then
            echo "  ✓ File contains data ($(wc -l < "$output_file") lines)"
            echo "  ✓ Processing data..."
        # Call the new processing script with the file and its directory as arguments
        ./processInternalCompetitionData.sh "$output_file" "$season_dir"
        else
            echo "  ⚠ Warning: Downloaded file is empty"
        fi
    else
        echo "  ✗ Failed to download from: $url"
    fi

    echo ""
    rm $output_file
done

echo "Import completed!"