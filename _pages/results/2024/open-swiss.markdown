---
layout: single
title:  "2024 Open Swiss"
permalink: "/results/2024/open-swiss.html"
toc: true
toc_sticky: true
sidebar:
  nav: results
---

<dl class="dl-horizontal">
	<dt>Tournament director:</dt>
	<dd>
		{% include snippets/member_link.html value="adrian-elwin" field="slug" %}
	</dd>
	<dt>Time control:</dt>
	<dd>35 moves in 70 minutes plus 10 minutes to finish the game together with a 10 second increment from move 1.</dd>
</dl>

{% assign tourney = site.data.results.internal[ "2024" ].openswiss %}
{% include snippets/swiss_tournament.html data=tourney %}
