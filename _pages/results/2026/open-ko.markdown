---
layout: single
title:  "2026 Open Knockout"
permalink: "/results/2026/open-ko.html"
toc: true
toc_sticky: true
---

{% capture rules %}
{% include snippets/standard_ko_rules.html %}
{% endcapture %}

{% assign tourney = site.data.results.internal[ "2026" ].openko %}
{% include snippets/ko_tournament.html data=tourney director="adrian-elwin" timecontrol="Time control is game in 80 minutes with a 10 secs/move increment from move 1." rules=rules %}
