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

Adrian Elwin, Alan Heath, Giuseppe Spigapiena and Vincent Edwards finished level on 2½. A mini-knockout resolved the tie.

{% include snippets/all_play_all_toggle_table.html results=pool3 %}

### Playoff

The playoff was two semi-finals, then a final played whih took two attempts to resolve, Adrian making the way through to the final group.

#### Semi-finals

<table class="swiss-results-table">
	<thead>
		<tr>
			<th class="text-right">White</th>
			<th class="swiss-result">vs</th>
			<th>Black</th>
			<th>Date</th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td class="text-right">{% include snippets/member_link.html value="adrian-elwin" field="slug" %}</td>
			<td class="swiss-result">{% include snippets/result.html result="1-0" %}</td>
			<td>{% include snippets/member_link.html value="vincent-edwards" field="slug" %}</td>
			<td>20 Aug, 2026</td>
		</tr>
		<tr>
			<td class="text-right">{% include snippets/member_link.html value="alan-heath" field="slug" %}</td>
			<td class="swiss-result">{% include snippets/result.html result="0-1" %}</td>
			<td>{% include snippets/member_link.html value="giuseppe-spigapiena" field="slug" %}</td>
			<td>16 Sep, 2026</td>
		</tr>
	</tbody>
</table>

#### Playoff final

<table class="swiss-results-table">
	<thead>
		<tr>
			<th class="text-right">White</th>
			<th class="swiss-result">vs</th>
			<th>Black</th>
			<th>Date</th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td class="text-right">{% include snippets/member_link.html value="giuseppe-spigapiena" field="slug" %}</td>
			<td class="swiss-result">{% include snippets/result.html result="1/2-1/2" %}</td>
			<td>{% include snippets/member_link.html value="adrian-elwin" field="slug" %}</td>
			<td>22 Oct, 2026</td>
		</tr>
		<tr>
			<td class="text-right">{% include snippets/member_link.html value="adrian-elwin" field="slug" %}</td>
			<td class="swiss-result">{% include snippets/result.html result="1-0" %}</td>
			<td>{% include snippets/member_link.html value="giuseppe-spigapiena" field="slug" %}</td>
			<td>12 Nov, 2026</td>
		</tr>
	</tbody>
</table>

## Pool 4

{% include snippets/all_play_all_toggle_table.html results=pool4 %}
