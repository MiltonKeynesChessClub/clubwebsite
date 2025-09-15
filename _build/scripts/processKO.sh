#!/bin/bash

CSV_FILE="$1"
ROOT_DIR="$2"
SLUG="$3"

if [[ ! -f "$CSV_FILE" ]]; then
    echo "CSV file not found: $CSV_FILE"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$ROOT_DIR/$SLUG"

# Generate pairings.csv
echo "pool,round,white,black,date,result" > "$ROOT_DIR/$SLUG/pairings.csv"

# Process CSV to generate pairings
awk -F',' -v OFS=',' '
NR == 1 { next }  # Skip header
{
    tournament = $1
    format = $2
    pool = $3
    round = $4
    white = $6
    black = $8
    date = $10
    result = $11

    # Strip whitespace from result
    gsub(/^[ \t\r\n]+|[ \t\r\n]+$/, "", result)

    # Skip if not a KO tournament or if missing required fields
    if (format != "ko" || white == "" || pool == "") next

    # Skip entries with malformed names (containing "/" or incomplete)
    if (white ~ /\// || white ~ /^[[:space:]]*$/) next

    # For bye results, allow empty black player
    if (result != "bye" && (black == "" || black ~ /\// || black ~ /^[[:space:]]*$/)) next

    # Handle defaulted results
    if (result == "black defaulted") {
        result = "1-def"
    } else if (result == "white defaulted") {
        result = "def-1"
    }

    print pool, round, white, black, date, result
}' "$CSV_FILE" >> "$ROOT_DIR/$SLUG/pairings.csv"

echo "Generated pairings.csv for $SLUG tournament"