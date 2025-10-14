---
title: Publications
layout: default
permalink: /publications/
---

{% assign pubs = site.data.publications | default: [] %}

<section class="pubs-page">
  <h2 class="pubs-title">Selected publications</h2>
  {% assign picks = pubs | where: "selected_publication", true %}
  {% if picks.size > 0 %}
    {% assign picks_sorted = picks | sort: "year" | reverse %}
    <div class="pub-grid">
      {% for p in picks_sorted %}
        <article class="pub-card">
          {% if p.image %}
            <a class="pub-thumb" href="{{ p.venue_link | default: '#' }}" {% if p.venue_link %}target="_blank" rel="noopener"{% endif %}>
              <img loading="lazy" src="{{ p.image | relative_url }}" alt="{{ p.title | escape }}">
            </a>
          {% endif %}
          <div class="pub-body">
            <h3 class="pub-head">{{ p.title }}</h3>
            <div class="pub-meta">{{ p.authors }}</div>
            <div class="pub-venue">
              {% if p.venue_link %}
                <a href="{{ p.venue_link }}" target="_blank" rel="noopener">{{ p.venue }}</a>
              {% else %}
                {{ p.venue }}
              {% endif %}
              {% if p.year %} · {{ p.year }}{% endif %}
            </div>
          </div>
        </article>
      {% endfor %}
    </div>
  {% else %}
    <p>No selected publications yet.</p>
  {% endif %}

  <hr class="pub-divider">

  <h2 class="pubs-title">All publications</h2>
  {% if pubs.size > 0 %}
    {% assign sorted = pubs | sort: "year" | reverse %}
    <div class="pub-stack">
      {% for p in sorted %}
        <article class="pub-row">
          <div class="pub-row-main">
            <h4 class="pub-row-title">{{ p.title }}</h4>
            <div class="pub-row-authors">{{ p.authors }}</div>
            <div class="pub-row-venue">
              {% if p.venue_link %}
                <a href="{{ p.venue_link }}" target="_blank" rel="noopener">{{ p.venue }}</a>
              {% else %}
                {{ p.venue }}
              {% endif %}
              {% if p.year %} · {{ p.year }}{% endif %}
            </div>
          </div>
          {% if p.image %}
            <a class="pub-row-thumb" href="{{ p.venue_link | default: '#' }}" {% if p.venue_link %}target="_blank" rel="noopener"{% endif %}>
              <img loading="lazy" src="{{ p.image | relative_url }}" alt="{{ p.title | escape }}">
            </a>
          {% endif %}
        </article>
      {% endfor %}
    </div>
  {% else %}
    <p>Publications will appear here after the first sync.</p>
  {% endif %}
</section>
