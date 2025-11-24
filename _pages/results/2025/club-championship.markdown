---
layout: single
title:  "2025 Club Championship"
permalink: "/results/2025/club-championship.html"
toc: true
toc_sticky: true
---

{% assign final = site.data.results.internal[ "2025" ].championship.final %}
{% assign pool1 = site.data.results.internal[ "2025" ].championship.pool1 %}
{% assign pool2 = site.data.results.internal[ "2025" ].championship.pool2 %}
{% assign pool3 = site.data.results.internal[ "2025" ].championship.pool3 %}
{% assign pool4 = site.data.results.internal[ "2025" ].championship.pool4 %}

{% capture rules %}
In each pool, all players play each other. See pairings chart for colour.
The top player from each group to go through to the Final as will the best 2 second placed players.
All ties will be resolved by a normal-speed playoff game and then, if necessary, pairs of rapid-play game.
{% endcapture %}

{% include snippets/tourney_info.html rules=rules director="adrian-elwin" timecontrol="Time control is game in 80 minutes with a 10 secs/move increment from move 1." %}

# Final pool

{% include snippets/all_play_all_toggle_table.html results=final %}

# First round stage

Initial pool games to be played by 22nd August 2025.

## Pool 1 (completed)

{% include snippets/all_play_all_toggle_table.html results=pool1 %}

## Pool 2 (completed)

{% include snippets/all_play_all_toggle_table.html results=pool2 %}

## Pool 3 (completed)

{% include snippets/all_play_all_toggle_table.html results=pool3 %}

## Pool 4

{% include snippets/all_play_all_toggle_table.html results=pool4 %}
