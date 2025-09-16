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
echo "Name,Rating,Score,Played" > "$ROOT_DIR/$SLUG/players.csv"

# Function to calculate points from result
calculate_points() {
    local result="$1"
    local player_color="$2"  # "white" or "black"

    case "$result" in
        "1-0")
            if [[ "$player_color" == "white" ]]; then echo "1"; else echo "0"; fi
            ;;
        "0-1")
            if [[ "$player_color" == "white" ]]; then echo "0"; else echo "1"; fi
            ;;
        "1/2-1/2")
            echo "0.5"
            ;;
        "bye")
            if [[ "$player_color" == "white" ]]; then echo "1"; else echo "0"; fi
            ;;
        "white defaulted")
            if [[ "$player_color" == "white" ]]; then echo "0"; else echo "1"; fi
            ;;
        "black defaulted")
            if [[ "$player_color" == "white" ]]; then echo "1"; else echo "0"; fi
            ;;
        "tbc")
            echo "0"
            ;;
        *)
            echo "0"
            ;;
    esac
}

# Process CSV with awk to generate players.csv
awk -F',' -v OFS=',' '
NR == 1 { next }  # Skip header
{
    white_name = $6
    white_rating = $7
    black_name = $8
    black_rating = $9
    result = $11
    gsub(/^[ \t\r\n]+|[ \t\r\n]+$/, "", result)  # Strip whitespace

    # Skip bye entries
    if (white_name == "bye" || black_name == "bye") next

    # Calculate points
    white_pts = 0
    black_pts = 0

    if (result == "1-0") {
        white_pts = 1
    } else if (result == "0-1") {
        black_pts = 1
    } else if (result == "1/2-1/2") {
        white_pts = 0.5
        black_pts = 0.5
    } else if (result == "bye") {
        white_pts = 1
    } else if (result == "1/2 pt bye") {
        white_pts = 0.5
    } else if (result == "white defaulted") {
        black_pts = 1
    } else if (result == "black defaulted") {
        white_pts = 1
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
            # Increment games played for white player
            if (white_name in games_played) {
                games_played[white_name]++
            } else {
                games_played[white_name] = 1
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
            # Increment games played for black player
            if (black_name in games_played) {
                games_played[black_name]++
            } else {
                games_played[black_name] = 1
            }
        }
    } else {
        # For tbc games, just store ratings
        if (white_name != "" && !(white_name in first_rating)) {
            first_rating[white_name] = white_rating
            if (!(white_name in total_score)) {
                total_score[white_name] = 0
            }
            if (!(white_name in games_played)) {
                games_played[white_name] = 0
            }
        }
        if (black_name != "" && !(black_name in first_rating)) {
            first_rating[black_name] = black_rating
            if (!(black_name in total_score)) {
                total_score[black_name] = 0
            }
            if (!(black_name in games_played)) {
                games_played[black_name] = 0
            }
        }
    }
}
END {
    # Output all players
    for (player in total_score) {
        rating = first_rating[player]
        if (rating == "0" || rating == "") {
            rating = "ur"
        }
        played = games_played[player]
        if (played == "") {
            played = 0
        }
        print player "," rating "," total_score[player] "," played
    }
}' "$CSV_FILE" | sort -t',' -k3,3nr -k2,2nr >> "$ROOT_DIR/$SLUG/players.csv"

echo "Generated players.csv for $SLUG tournament"

# Generate pairings.csv
echo "round,board,white,black,whitepts,blackpts,date,result" > "$ROOT_DIR/$SLUG/pairings.csv"

# Process pairings with cumulative points
awk -F',' -v OFS=',' '
NR == 1 { next }  # Skip header
{
    round = $4
    board = $5
    white = $6
    black = $8
    date = $10
    result = $11
    gsub(/^[ \t\r\n]+|[ \t\r\n]+$/, "", result)  # Strip whitespace

    # Skip bye entries
    if (white == "bye" || black == "bye") next

    # Store game data
    games[round][board] = white "," black "," date "," result
}
END {
    # Generate pairings with cumulative points
    for (round_num = 1; round_num <= 10; round_num++) {
        if (round_num in games) {
            for (board_num in games[round_num]) {
                split(games[round_num][board_num], game_data, ",")
                white = game_data[1]
                black = game_data[2]
                date = game_data[3]
                result = game_data[4]

                # Calculate cumulative points going into this round
                white_cumulative = ""
                black_cumulative = ""

                if (round_num == 1) {
                    white_cumulative = ""
                    black_cumulative = ""
                } else {
                    # Calculate points from previous rounds
                    white_prev_points = 0
                    black_prev_points = 0
                    white_missing = 0
                    black_missing = 0

                    for (prev_round = 1; prev_round < round_num; prev_round++) {
                        if (prev_round in games) {
                            for (prev_board in games[prev_round]) {
                                split(games[prev_round][prev_board], prev_game_data, ",")
                                prev_white = prev_game_data[1]
                                prev_black = prev_game_data[2]
                                prev_result = prev_game_data[4]
                                gsub(/^[ \t\r\n]+|[ \t\r\n]+$/, "", prev_result)  # Strip whitespace

                                # Calculate points from result
                                prev_white_pts = 0
                                prev_black_pts = 0
                                is_completed = 0

                                if (prev_result == "1-0") {
                                    prev_white_pts = 1
                                    prev_black_pts = 0
                                    is_completed = 1
                                } else if (prev_result == "0-1") {
                                    prev_white_pts = 0
                                    prev_black_pts = 1
                                    is_completed = 1
                                } else if (prev_result == "1/2-1/2") {
                                    prev_white_pts = 0.5
                                    prev_black_pts = 0.5
                                    is_completed = 1
                                } else if (prev_result == "bye") {
                                    prev_white_pts = 1
                                    prev_black_pts = 0
                                    is_completed = 1
                                } else if (prev_result == "1/2 pt bye") {
                                    prev_white_pts = 0.5
                                    prev_black_pts = 0
                                    is_completed = 1
                                } else if (prev_result == "white defaulted") {
                                    prev_white_pts = 0
                                    prev_black_pts = 1
                                    is_completed = 1
                                } else if (prev_result == "black defaulted") {
                                    prev_white_pts = 1
                                    prev_black_pts = 0
                                    is_completed = 1
                                } else if (prev_result == "game defaulted") {
                                    prev_white_pts = 0
                                    prev_black_pts = 0
                                    is_completed = 1
                                } else if (prev_result == "tbc") {
                                    is_completed = 0
                                }

                                # Add points for current player
                                if (prev_white == white) {
                                    if (is_completed) {
                                        white_prev_points += prev_white_pts
                                    } else {
                                        white_missing++
                                    }
                                }
                                if (prev_black == white) {
                                    if (is_completed) {
                                        white_prev_points += prev_black_pts
                                    } else {
                                        white_missing++
                                    }
                                }
                                if (prev_white == black) {
                                    if (is_completed) {
                                        black_prev_points += prev_white_pts
                                    } else {
                                        black_missing++
                                    }
                                }
                                if (prev_black == black) {
                                    if (is_completed) {
                                        black_prev_points += prev_black_pts
                                    } else {
                                        black_missing++
                                    }
                                }
                            }
                        }
                    }

                    # Format cumulative points with + suffix for missing results
                    if (white_prev_points > 0 || white_missing > 0) {
                        white_cumulative = white_prev_points
                        for (i = 1; i <= white_missing; i++) {
                            white_cumulative = white_cumulative "+"
                        }
                    } else if (round_num > 1) {
                        white_cumulative = "0"
                    }

                    if (black_prev_points > 0 || black_missing > 0) {
                        black_cumulative = black_prev_points
                        for (i = 1; i <= black_missing; i++) {
                            black_cumulative = black_cumulative "+"
                        }
                    } else if (round_num > 1) {
                        black_cumulative = "0"
                    }
                }

                # Transform result for output
                output_result = result
                if (result == "white defaulted") {
                    output_result = "def-1"
                } else if (result == "black defaulted") {
                    output_result = "1-def"
                } else if (result == "1/2 pt bye") {
                    output_result = "bye"
                } else if (result == "game defaulted") {
                    output_result = "def-def"
                }

                print round_num "," board_num "," white "," black "," white_cumulative "," black_cumulative "," date "," output_result
            }
        }
    }
}' "$CSV_FILE" >> "$ROOT_DIR/$SLUG/pairings.csv"

echo "Generated pairings.csv for $SLUG tournament"

# Update rounds.csv if it exists
if [[ -f "$ROOT_DIR/$SLUG/rounds.csv" ]]; then
    echo "Updating rounds.csv for $SLUG tournament"

    temp_rounds=$(mktemp)

    # Process rounds.csv and update flags based on source data
    awk -F',' -v csv_file="$CSV_FILE" '
    BEGIN {
        # Read the source CSV to determine round status
        while ((getline line < csv_file) > 0) {
            if (NR == 1) continue  # Skip header
            split(line, fields, ",")
            round_num = fields[4]
            result = fields[11]
            gsub(/^[ \t\r\n]+|[ \t\r\n]+$/, "", result)  # Strip whitespace

            rounds_in_source[round_num] = 1

            if (result == "tbc") {
                rounds_incomplete[round_num] = 1
            }
        }
        close(csv_file)
    }
    {
        if (NR == 1) {
            print $0
            next
        }

        round_num = $1
        complete = $2
        active = $3
        deadline = $4

        if (round_num in rounds_in_source) {
            if (round_num in rounds_incomplete) {
                complete = "false"
                active = "true"
            } else {
                complete = "true"
                active = "false"
            }
        } else {
            complete = "false"
            active = "false"
        }

        print round_num "," complete "," active "," deadline
    }' "$ROOT_DIR/$SLUG/rounds.csv" > "$temp_rounds"

    mv "$temp_rounds" "$ROOT_DIR/$SLUG/rounds.csv"
    echo "Updated rounds.csv with active/completed flags"
else
    echo "No rounds.csv found for $SLUG tournament"
fi