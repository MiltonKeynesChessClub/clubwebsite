---
layout: single
title:  "2026 Club Championship"
permalink: "/results/2026/club-championship.html"
toc: true
toc_sticky: true
---

{% assign final = site.data.results.internal[ "2026" ].championship.final %}
{% assign pool1 = site.data.results.internal[ "2026" ].championship.pool1 %}
{% assign pool2 = site.data.results.internal[ "2026" ].championship.pool2 %}
{% assign pool3 = site.data.results.internal[ "2026" ].championship.pool3 %}
{% assign pool4 = site.data.results.internal[ "2026" ].championship.pool4 %}

{% capture rules %}
In each pool, all players play each other. See pairings chart for colour.
The top player from each group to go through to the Final as will the best 2 second placed players.
All ties will be resolved by a normal-speed playoff game and then, if necessary, pairs of rapid-play game.
{% endcapture %}

{% include snippets/tourney_info.html rules=rules director="adrian-elwin" timecontrol="Time control is game in 80 minutes with a 10 secs/move increment from move 1." %}

# Final pool

Andrew Bowler, Joseph Asante and James Alexander won their pools. Eric Meichel and George Ward also qualified. Adrian Elwin took the pool 3 place after a mini-knockout broke a four-way tie.

{% include snippets/all_play_all_toggle_table.html results=final %}

# First round stage

## Pool 1

{% include snippets/all_play_all_toggle_table.html results=pool1 %}

## Pool 2

{% include snippets/all_play_all_toggle_table.html results=pool2 %}

## Pool 3

Adrian Elwin, Alan Heath, Giuseppe Spigapiena and Vincent Edwards finished level on 2½. A mini-knockout resolved the tie, and Adrian Elwin progresses to the final.

{% include snippets/all_play_all_toggle_table.html results=pool3 %}

## Pool 4

{% include snippets/all_play_all_toggle_table.html results=pool4 %}
