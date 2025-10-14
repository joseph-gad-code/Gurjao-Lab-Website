---
title: "Publications"
layout: default
permalink: /publications/
---

<h1>Selected publications</h1>

<div class="pubs-selected">
{% assign pubs = site.data.publications %}
{% for p in pubs %}
  {% assign flag = p["selected-publication"] | downcase %}
  {% if flag == "yes" %}
  <article class="pub-card">
    {% if p.image %}
    <div class="pub-thumb">
      <img loading="lazy" src="{{ p.image | relative_url }}" alt="{{ p.title | escape }}">
    </div>
    {% endif %}
    <div class="pub-body">
      <h3 class="pub-title">
        {% if p.url %}<a href="{{ p.url }}" target="_blank" rel="noopener">{{ p.title }}</a>{% else %}{{ p.title }}{% endif %}
      </h3>

      {% assign labnames = site.data.people | map: "name" %}
      {% capture authors_html %}{{ p.authors }}{% endcapture %}
      {% for nm in labnames %}
        {% assign authors_html = authors_html | replace: nm, '<strong>' | append: nm | append: '</strong>' %}
      {% endfor %}
      <div class="pub-authors">{{ authors_html | strip_newlines }}</div>

      <div class="pub-venue">
        {% if p.venue %}
          {% if p.url %}<a href="{{ p.url }}" target="_blank" rel="noopener">{{ p.venue }}</a>{% else %}{{ p.venue }}{% endif %}
          {% if p.year %}, {{ p.year }}{% endif %}
        {% endif %}
      </div>
    </div>
  </article>
  {% endif %}
{% endfor %}
</div>

<h2>Full list</h2>

{% assign ordered = pubs | sort: "year" | reverse %}
{% assign years = ordered | map: "year" | uniq %}

{% for y in years %}
  {% if y %}
  <h3 class="pub-year">{{ y }}</h3>
  <div class="pub-year-list">
    {% for p in ordered %}
      {% if p.year == y %}
      <article class="pub-row">
        <div class="pub-row-title">
          {% if p.url %}<a href="{{ p.url }}" target="_blank" rel="noopener">{{ p.title }}</a>{% else %}{{ p.title }}{% endif %}
        </div>

        {% assign labnames = site.data.people | map: "name" %}
        {% capture authors2 %}{{ p.authors }}{% endcapture %}
        {% for nm in labnames %}
          {% assign authors2 = authors2 | replace: nm, '<strong>' | append: nm | append: '</strong>' %}
        {% endfor %}
        <div class="pub-row-authors">{{ authors2 | strip_newlines }}</div>

        <div class="pub-row-venue">
          {% if p.venue %}
            {% if p.url %}<a href="{{ p.url }}" target="_blank" rel="noopener">{{ p.venue }}</a>{% else %}{{ p.venue }}{% endif %}
          {% endif %}
        </div>
      </article>
      {% endif %}
    {% endfor %}
  </div>
  {% endif %}
{% endfor %}
