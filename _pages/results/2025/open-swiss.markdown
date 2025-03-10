---
layout: single
title:  "2025 Open Swiss"
permalink: "/results/2025/open-swiss.html"
toc: true
toc_sticky: true
---

{% assign tourney = site.data.results.internal[ "2025" ].openswiss %}
{% include snippets/swiss_tournament.html data=tourney director="adrian-elwin" timecontrol="Time control is game in 80 minutes with a 10 secs/move increment from move 1." %}
