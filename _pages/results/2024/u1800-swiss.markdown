---
layout: single
title:  "U1800 Swiss"
permalink: "/results/2024/u1800-swiss.html"
toc: true
toc_sticky: true
sidebar:
  nav: results
---

{% assign tourney = site.data.results.internal[ "2024" ].u1800swiss %}
{% include snippets/swiss_tournament.html data=tourney director="adrian-elwin" timecontrol="35 moves in 70 minutes plus 10 minutes to finish the game together with a 10 second increment from move 1." %}
