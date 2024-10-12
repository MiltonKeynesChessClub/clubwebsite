---
layout: single
title:  "Results and Tables"
permalink: /results/
toc: true
toc_sticky: true
sidebar:
  nav: results
---

Here you can find this season's results and pairings for Milton Keynes Chess Club internal competitions. You will also find team results and standings for each of our teams in the [Bedfordshire Chess League](https://lms.englishchess.org.uk/lms/organisation/308).

{% for section in site.data.navigation.results %}
## {{ section.title }}
	{% for p in section.children %}
* [{{ p.title }}]({{ p.url }})
	{% endfor %}
{% endfor %}