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

# Get list of pools from the data
pools=$(awk -F',' 'NR == 1 { next } $2 == "championship" && $3 != "" { print $3 }' "$CSV_FILE" | sort | uniq)

echo "Found pools: $pools"

# Process each pool
for pool in $pools; do
    echo "Processing pool: $pool"

    # Create pool directory
    mkdir -p "$ROOT_DIR/$SLUG/$pool"

    # Generate pairings.csv for this pool
    echo "pool,round,white,black,date,result" > "$ROOT_DIR/$SLUG/$pool/pairings.csv"

    awk -F',' -v target_pool="$pool" -v OFS=',' '
    NR == 1 { next }  # Skip header
    $2 == "championship" && $3 == target_pool {
        pool = $3
        round = $4
        white = $6
        black = $8
        date = $10
        result = $11

        # Strip whitespace from result
        gsub(/^[ \t\r\n]+|[ \t\r\n]+$/, "", result)

        # Skip if missing required fields
        if (white == "" || black == "") next

        # Transform result for output
        output_result = result
        if (result == "white defaulted") {
            output_result = "def-1"
        } else if (result == "black defaulted") {
            output_result = "1-def"
        }

        print pool, round, white, black, date, output_result
    }' "$CSV_FILE" >> "$ROOT_DIR/$SLUG/$pool/pairings.csv"

    # Generate players.csv for this pool
    echo "name,rating,score,place" > "$ROOT_DIR/$SLUG/$pool/players.csv"

    awk -F',' -v target_pool="$pool" -v OFS=',' '
    NR == 1 { next }  # Skip header
    $2 == "championship" && $3 == target_pool {
        white_name = $6
        white_rating = $7
        black_name = $8
        black_rating = $9
        result = $11

        # Strip whitespace from result
        gsub(/^[ \t\r\n]+|[ \t\r\n]+$/, "", result)

        # Skip if missing required fields
        if (white_name == "" || black_name == "") next

        # Check if pool is complete (no tbc results)
        if (result == "tbc") {
            pool_complete = 0
        }

        # Calculate points from result
        white_pts = 0
        black_pts = 0

        if (result == "1-0") {
            white_pts = 1
            black_pts = 0
        } else if (result == "0-1") {
            white_pts = 0
            black_pts = 1
        } else if (result == "1/2-1/2") {
            white_pts = 0.5
            black_pts = 0.5
        } else if (result == "bye") {
            white_pts = 1
            black_pts = 0
        } else if (result == "white defaulted") {
            white_pts = 0
            black_pts = 1
        } else if (result == "black defaulted") {
            white_pts = 1
            black_pts = 0
        }

        # Only count points for completed games
        if (result != "tbc") {
            # Process white player
            if (white_name != "") {
                if (!(white_name in first_rating)) {
                    first_rating[white_name] = white_rating
                }
                if (white_name in total_score) {
                    total_score[white_name] += white_pts
                } else {
                    total_score[white_name] = white_pts
                }
            }

            # Process black player
            if (black_name != "") {
                if (!(black_name in first_rating)) {
                    first_rating[black_name] = black_rating
                }
                if (black_name in total_score) {
                    total_score[black_name] += black_pts
                } else {
                    total_score[black_name] = black_pts
                }
            }
        } else {
            # For tbc games, just store ratings
            if (white_name != "" && !(white_name in first_rating)) {
                first_rating[white_name] = white_rating
                if (!(white_name in total_score)) {
                    total_score[white_name] = 0
                }
            }
            if (black_name != "" && !(black_name in first_rating)) {
                first_rating[black_name] = black_rating
                if (!(black_name in total_score)) {
                    total_score[black_name] = 0
                }
            }
        }
    }
    END {
        # Initialize pool as complete (will be set to 0 if any tbc found)
        if (pool_complete == "") pool_complete = 1

        # Create array of players with scores for sorting
        player_count = 0
        for (player in total_score) {
            player_count++
            players[player_count] = player
            scores[player] = total_score[player]
            ratings[player] = first_rating[player]
        }

        # Sort players by score (desc) then rating (desc)
        for (i = 1; i <= player_count; i++) {
            for (j = i + 1; j <= player_count; j++) {
                if (scores[players[i]] < scores[players[j]] ||
                    (scores[players[i]] == scores[players[j]] && ratings[players[i]] < ratings[players[j]])) {
                    temp = players[i]
                    players[i] = players[j]
                    players[j] = temp
                }
            }
        }

        # Calculate places if pool is complete
        if (pool_complete) {
            current_place = 1
            for (i = 1; i <= player_count; i++) {
                if (i <= 3) {  # Only top 3 get places
                    if (i > 1 && scores[players[i]] == scores[players[i-1]]) {
                        # Tie - use same place as previous
                        place = place
                    } else {
                        place = current_place
                    }

                    # Convert place number to ordinal
                    if (place == 1) {
                        place_ordinal = "1st"
                    } else if (place == 2) {
                        place_ordinal = "2nd"
                    } else if (place == 3) {
                        place_ordinal = "3rd"
                    }

                    if (i > 1 && scores[players[i]] == scores[players[i-1]]) {
                        place_str = "=" place_ordinal
                    } else {
                        place_str = place_ordinal
                    }
                } else {
                    place_str = ""
                }

                rating = ratings[players[i]]
                if (rating == "0" || rating == "") {
                    rating = "ur"
                }

                print players[i] "," rating "," scores[players[i]] "," place_str
                current_place++
            }
        } else {
            # Pool not complete - no places
            for (i = 1; i <= player_count; i++) {
                rating = ratings[players[i]]
                if (rating == "0" || rating == "") {
                    rating = "ur"
                }
                print players[i] "," rating "," scores[players[i]] ","
            }
        }
    }' "$CSV_FILE" >> "$ROOT_DIR/$SLUG/$pool/players.csv"

    echo "Generated files for pool: $pool"
done

echo "Generated championship tournament files for $SLUG"