---
title: "Publications"
layout: default
permalink: /publications/
---

<section class="publications-page">

  <h1 class="pubs-title">Publications</h1>

  {% assign pubs = site.data.publications | sort: "year" | reverse %}

  {% assign featured = pubs | where_exp: "p", "p.selected_publication == true" %}
  {% if featured and featured.size > 0 %}
  <h2 class="pubs-subtitle">Selected publications</h2>

  <div class="pub-grid">
    {% for p in featured %}
    <article class="pub-card">
      {% if p.image %}
      <div class="pub-card-media">
        <img src="{{ p.image | relative_url }}" alt="{{ p.title | escape }}">
      </div>
      {% endif %}

      <div class="pub-card-body">
        <h3 class="pub-card-title">{{ p.title }}</h3>
        <div class="pub-card-authors">{{ p.authors }}</div>

        <div class="pub-card-meta">
          {% if p.url and p.journal %}
            <a href="{{ p.url }}" target="_blank" rel="noopener">{{ p.journal }}</a>
          {% else %}
            {{ p.journal }}
          {% endif %}
          {% if p.year %} · {{ p.year }}{% endif %}
          {% if p.doi %} · <a href="https://doi.org/{{ p.doi }}" target="_blank" rel="noopener">DOI</a>{% endif %}
        </div>
      </div>
    </article>
    {% endfor %}
  </div>
  {% endif %}

  <h2 class="pubs-subtitle">All publications</h2>

  {% assign years = pubs | map: "year" | uniq | sort | reverse %}
  {% for y in years %}
    {% assign group = pubs | where: "year", y %}
    {% if group and group.size > 0 %}
      <h3 class="pubs-year">{{ y }}</h3>
      <div class="pub-list">
        {% for p in group %}
        <article class="pub-list-item">
          <h4 class="pub-li-title">{{ p.title }}</h4>
          <div class="pub-li-authors">{{ p.authors }}</div>
          <div class="pub-li-meta">
            {% if p.url and p.journal %}
              <a href="{{ p.url }}" target="_blank" rel="noopener">{{ p.journal }}</a>
            {% else %}
              {{ p.journal }}
            {% endif %}
            {% if p.doi %} · <a href="https://doi.org/{{ p.doi }}" target="_blank" rel="noopener">DOI</a>{% endif %}
          </div>
        </article>
        {% endfor %}
      </div>
    {% endif %}
  {% endfor %}

</section>
