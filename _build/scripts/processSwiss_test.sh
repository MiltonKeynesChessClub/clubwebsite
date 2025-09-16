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

# Generate players.csv
echo "Name,Rating,Score" > "$ROOT_DIR/$SLUG/players.csv"

# Use awk to process the CSV and extract unique players with their data
awk -F',' '
BEGIN {
    # Skip header row
    getline
}
{
    # Process White player
    if ($6 != "" && $6 != "bye") {
        white_name = $6
        white_rating = $7
        result = $11

        # Calculate points from result
        white_pts = 0
        if (result == "1-0") {
            white_pts = 1
        } else if (result == "0-1") {
            white_pts = 0
        } else if (result == "1/2-1/2") {
            white_pts = 0.5
        } else if (result == "bye") {
            white_pts = 1
        } else if (result == "white defaulted") {
            white_pts = 0
        } else if (result == "black defaulted") {
            white_pts = 1
        } else if (result == "tbc") {
            white_pts = 0  # tbc games don't count for points
        }

        # Only process if we have a valid name and completed game
        if (white_name != "" && result != "tbc") {
            # Store first rating found for this player
            if (!(white_name in first_rating)) {
                first_rating[white_name] = white_rating
            }
            # Add to total score
            if (white_name in total_score) {
                total_score[white_name] += white_pts
            } else {
                total_score[white_name] = white_pts
            }
        } else if (white_name != "" && result == "tbc") {
            # Store first rating found for this player even if game not completed
            if (!(white_name in first_rating)) {
                first_rating[white_name] = white_rating
            }
            # Initialize total score if not exists
            if (!(white_name in total_score)) {
                total_score[white_name] = 0
            }
        }
    }
}
END {
    # Output all players
    for (player in total_score) {
        rating = first_rating[player]
        # Convert 0 rating to "ur" for unrated
        if (rating == "0" || rating == "") {
            rating = "ur"
        }
        print player "," rating "," total_score[player]
    }
}' "$CSV_FILE" | sort -t',' -k3,3nr -k2,2nr >> "$ROOT_DIR/$SLUG/players.csv"

echo "Generated players.csv for $SLUG tournament"

