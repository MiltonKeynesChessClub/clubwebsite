#! /bin/bash

# This script imports MK club players from the ECF ratings database
# and makes them available as raw data files for the Jekyll site.
# In addition, it stubs pages for the website for each player
# when they do not already exist.
#
# It depends on the following being available:
#
# * jq: https://jqlang.github.io/jq/
# * csvkit: https://csvkit.readthedocs.io/en/latest/

TMP_DIR=${TMP_DIR:-~/tmp}
TMP_ECF_CSV=$TMP_DIR/allplayers.csv
TMP_MK_ECF_CSV=$TMP_DIR/mkplayers.csv
TMP_MEMBER_JSON=$TMP_DIR/mkmembers.jsonl
MEMBER_CSV=../../_data/mkmembers.csv
ECF_DATA_DIR=../../_data/_generated
ECF_DATA_FILE=$ECF_DATA_DIR/mkmemberecfdata.json
MK_MEMBER_PAGES=../../members
ALL_CSV_HEADERS="\"ECF_code\",\"full_name\",\"member_no\",\"FIDE_no\",\"gender\",\"nation\",\"original_standard\",\"standard_original_category\",\"revised_standard\",\"standard_revised_category\",\"original_rapid\",\"rapid_origina l_category\",\"revised_rapid\",\"rapid_revised_category\",\"original_blitz\",\"blitz_original_category\",\"revised_blitz\",\"blitz_revised_category\",\"original_standard_online\",\"standard_online_original_ category\",\"revised_standard_online\",\"standard_online_revised_category\",\"original_rapid_online\",\"rapid_online_original_category\",\"revised_rapid_online\",\"rapid_online_revised_category\",\"origin al_blitz_online\",\"blitz_online_original_category\",\"revised_blitz_online\",\"blitz_online_revised_category\",\"club_code\",\"club_name\",\"title\""
LIMITED_HEADERS=ECF_code,full_name,revised_standard,standard_revised_category,revised_rapid,rapid_revised_category,revised_blitz,blitz_revised_category,title


function fetchFromEcf() {
	if [[ ! -f $TMP_ECF_CSV ]] ; then
		curl "https://rating.englishchess.org.uk/v2/new/api.php?v2/rating_list_csv" >> $TMP_ECF_CSV
	fi

	ECF_CODE=$1 # argument to function
	ECF_ENTRY=$( grep "$ECF_CODE" $TMP_ECF_CSV )

	if [[ -n $ECF_ENTRY ]] ; then
		echo $ECF_ENTRY
	fi
}

# reset temp files, etc
mkdir -p $MK_MEMBER_PAGES
echo "$ALL_CSV_HEADERS" > $TMP_MK_ECF_CSV

# Loop over our master members csv and lookup latest data from ECF
# and ensure a stub page exists for each member
csvjson --no-inference --stream $MEMBER_CSV > $TMP_MEMBER_JSON
while read member; do
	slug=$( echo $member | jq --raw-output '.slug' )
	name=$( echo $member | jq --raw-output '.name' )
	ecfcode=$( echo $member | jq --raw-output '.ecfcode' )

	# ensure stub page exists
	if [[ ! -f "${MK_MEMBER_PAGES}/${slug}.markdown" ]] ; then
  		echo "---
layout: member
title:  \"$name\"
member: $slug
---" > "${MK_MEMBER_PAGES}/${slug}.markdown"
  	fi

	# lookup additional data from ecf
	# if [[ -n $ecfcode ]] ; then
	# 	ecfentry=$( fetchFromEcf $ecfCode )
	# 	if [[ -n $ecfentry ]] ; then
	# 		echo $ecfentry >> $TMP_MK_ECF_CSV
	# 	fi
	# fi
done < $TMP_MEMBER_JSON

# Convert our TMP CSV into a json data file for Jekyll to use for additional data
mkdir -p $ECF_DATA_DIR
csvcut -c $LIMITED_HEADERS $TMP_MK_ECF_CSV | csvjson --indent 2 --no-inference -k ECF_code > $ECF_DATA_FILE