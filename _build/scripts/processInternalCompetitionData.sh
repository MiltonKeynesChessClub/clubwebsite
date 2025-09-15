#!/bin/bash

CSV_FILE="$1"
ROOT_DIR="$2"

if [[ ! -f "$CSV_FILE" ]]; then
    echo "CSV file not found: $CSV_FILE"
    exit 1
fi

# Get unique tournaments and their formats (skip header)
awk -F',' 'NR>1 {print $1 "|" $2}' "$CSV_FILE" | sort | uniq | while IFS='|' read -r tournament format; do
    # Skip empty tournament names
    if [[ -z "$tournament" ]]; then
        continue
    fi

    # Slugify tournament name for file naming
    slug=$(echo "$tournament" | tr '[:upper:]' '[:lower:]' | sed 's/ /_/g' | sed 's/[^a-z0-9_]//g')

    # Choose script based on format
    case "$format" in
        swiss)
            script="processSwiss.sh"
            ;;
        ko)
            script="processKO.sh"
            ;;
		ladder)
            script="processLadder.sh"
            ;;
        championship)
            script="processChampionship.sh"
            ;;
        *)
            echo "Unknown format '$format' for tournament '$tournament'. Skipping."
            continue
            ;;
    esac

    #Check if the script exists
    if [[ ! -x "./$script" ]]; then
        echo "Script not found or not executable: $script (needed for format '$format')"
        continue
    fi

    echo "Processing tournament '$tournament' (format: $format) with $script..."

    # Filter rows for this tournament (keep header)
    awk -F',' -v t="$tournament" 'NR==1 || $1==t' "$CSV_FILE" > "$ROOT_DIR/${slug}_data.csv"

    # # Call the appropriate script with the filtered CSV and root dir
    "./$script" "$ROOT_DIR/${slug}_data.csv" "$ROOT_DIR" "${slug}"

	rm "$ROOT_DIR/${slug}_data.csv"
done
