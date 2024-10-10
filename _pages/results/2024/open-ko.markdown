---
layout: single
title:  "2024 Open Knockout"
permalink: "/results/2024/open-ko.html"
toc: true
toc_sticky: true
sidebar:
  nav: results
---

{% capture rules %}
{% include snippets/standard_ko_rules.html %}
{% endcapture %}

{% assign tourney = site.data.results.internal[ "2024" ].openko %}
{% include snippets/ko_tournament.html data=tourney director="adrian-elwin" timecontrol="35 moves in 70 minutes plus 10 minutes to finish the game together with a 10 second increment from move 1." rules=rules %}