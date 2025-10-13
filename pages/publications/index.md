---
title: Publications
layout: default
permalink: /publications/
---

<section class="pubs-page">
  <h2 class="pubs-title">Selected publications</h2>

  {% assign allpubs = site.data.publications | default: [] %}

  {% assign selected = "" | split: "" %}
  {% for p in allpubs %}
    {% assign flag = p.selected_publication | default: p["selected-publication"] %}
    {% if flag == true or flag == 'true' or flag == 'yes' or flag == 'y' or flag == 1 %}
      {% assign selected = selected | push: p %}
    {% endif %}
  {% endfor %}

  {% if selected.size > 0 %}
    <div class="pub-grid">
      {% for p in selected %}
        <article class="pub-card">
          {% if p.image %}
            <a class="pub-thumb" href="{{ p.link | default: '#' }}" {% if p.link %}target="_blank" rel="noopener"{% endif %}>
              <img loading="lazy" src="{{ p.image | relative_url }}" alt="{{ p.title | escape }}">
            </a>
          {% endif %}
          <div class="pub-body">
            <h3 class="pub-head">
              {% if p.link %}<a href="{{ p.link }}" target="_blank" rel="noopener">{{ p.title }}</a>{% else %}{{ p.title }}{% endif %}
            </h3>
            <div class="pub-meta">{% if p.venue %}{{ p.venue }}{% endif %}{% if p.year %} · {{ p.year }}{% endif %}</div>
            {% if p.blurb %}<p class="pub-blurb">{{ p.blurb }}</p>{% endif %}
          </div>
        </article>
      {% endfor %}
    </div>
  {% else %}
    <p>No selected publications yet.</p>
  {% endif %}

  <hr class="pub-divider">

  <h2 class="pubs-title">All publications</h2>
  {% if allpubs.size > 0 %}
    {% assign sorted = allpubs | sort: "year" | reverse %}
    <ol class="pub-list">
      {% for item in sorted %}
        <li class="pub-item">
          <span class="pub-item-title">
            {% if item.link %}<a href="{{ item.link }}" target="_blank" rel="noopener">{{ item.title }}</a>{% else %}{{ item.title }}{% endif %}
          </span>
          {% if item.authors %}<span class="pub-authors"> — {{ item.authors }}</span>{% endif %}
          {% if item.venue or item.year %}<span class="pub-venue">{% if item.venue %} {{ item.venue }}{% endif %}{% if item.year %} {{ item.year }}{% endif %}</span>{% endif %}
        </li>
      {% endfor %}
    </ol>
  {% else %}
    <p>No publications to display.</p>
  {% endif %}
</section>
