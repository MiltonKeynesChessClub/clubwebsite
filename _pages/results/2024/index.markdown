---
layout: single
title:  "Results for 2024/2025"
permalink: "/results/2024"
excerpt: All our league and internal results for the 2024/25 season
toc: true
toc_sticky: true
---

Here you can find this season's results and pairings for Milton Keynes Chess Club internal competitions. You will also find team results and standings for each of our teams in the [Bedfordshire Chess League](https://lms.englishchess.org.uk/lms/organisation/308).

{% for section in site.data.navigation.results %}
## {{ section.title }}

<ul>
	{% for p in section.children %}
	<li><a href="{{ p.url }}">{{ p.title }}</a></li>
	{% endfor %}
</ul>
{% endfor %}