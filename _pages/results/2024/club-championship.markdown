---
layout: single
title:  "2024 Club Championship"
permalink: "/results/2024/club-championship.html"
toc: true
toc_sticky: true
sidebar:
  nav: results
---

{% assign finalpool = site.data.results.internal[ "2024" ].championship.finalpool %}
{% assign pool1 = site.data.results.internal[ "2024" ].championship.pool1 %}
{% assign pool2 = site.data.results.internal[ "2024" ].championship.pool2 %}
{% assign pool3 = site.data.results.internal[ "2024" ].championship.pool3 %}
{% assign pool4 = site.data.results.internal[ "2024" ].championship.pool4 %}

{% capture rules %}
In each pool, all players play each other. See pairings chart for colour.
The top player from each group to go through to the Final as will the best 2 second placed players.
All ties will be resolved by a normal-speed playoff game and then, if necessary, pairs of rapid-play game.
{% endcapture %}

{% include snippets/tourney_info.html rules=rules director="adrian-elwin" timecontrol="35 moves in 70 minutes plus 10 minutes to finish the game together with a 10 second increment from move 1." %}

# Final pool

Final pool to be played by 31st December 2024. Anybody having problems meeting the date should keep me informed.

{% include snippets/all_play_all_table.html results=finalpool %}


# First round stage

## Pool 1

{% include snippets/all_play_all_table.html results=pool1 %}

## Pool 2

{% include snippets/all_play_all_table.html results=pool2 %}

## Pool 3

{% include snippets/all_play_all_table.html results=pool3 %}

## Pool 4

{% include snippets/all_play_all_table.html results=pool4 %}
