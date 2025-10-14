---
title: "Publications"
layout: default
permalink: /publications/
---

<section class="pubs-page">
  <h1>Publications</h1>

  {% assign pubs = site.data.publications %}
  {% if pubs and pubs.size > 0 %}

  {% comment %} Selected publications (cards, 2 columns) {% endcomment %}
  {% assign selected = pubs | where: "selected_publication", true %}
  {% if selected.size > 0 %}
  <h2 class="pubs-subtitle">Selected publications</h2>
  <div class="pub-cards">
    {% for p in selected %}
      <article class="pub-card">
        {% if p.image %}
          <div class="pub-card-media">
            <img src="{{ p.image | relative_url }}" alt="{{ p.title | escape }}">
          </div>
        {% endif %}
        <div class="pub-card-body">
          <h3 class="pub-title">{{ p.title }}</h3>
          <div class="pub-authors">{{ p.authors }}</div>
          <div class="pub-meta">
            {% if p.journal and p.url %}
              <a href="{{ p.url }}" target="_blank" rel="noopener">{{ p.journal }}</a>
            {% elsif p.journal %}
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

  {% comment %} All publications grouped by year (newest first), unnumbered {% endcomment %}
  <h2 class="pubs-subtitle">All publications</h2>
  {% assign sorted = pubs | sort: "year" | reverse %}

  {% assign current_year = "" %}
  {% for p in sorted %}
    {% if p.year != current_year %}
      {% unless forloop.first %}</ul>{% endunless %}
      <h3 class="pubs-year">{{ p.year }}</h3>
      <ul class="pubs-list">
      {% assign current_year = p.year %}
    {% endif %}
    <li class="pubs-item">
      <div class="pubs-item-title">{{ p.title }}</div>
      <div class="pubs-item-meta">
        <span class="pubs-item-authors">{{ p.authors }}</span>
        {% if p.journal and p.url %}
          · <a href="{{ p.url }}" target="_blank" rel="noopener">{{ p.journal }}</a>
        {% elsif p.journal %}
          · {{ p.journal }}
        {% endif %}
        {% if p.doi %} · <a href="https://doi.org/{{ p.doi }}" target="_blank" rel="noopener">DOI</a>{% endif %}
      </div>
    </li>
    {% if forloop.last %}</ul>{% endif %}
  {% endfor %}

  {% else %}
    <p>No publications found.</p>
  {% endif %}
</section>
