---
title: Publications
layout: default
permalink: /publications/
---

# Publications

{%- comment -%}
Load data. Accept either:
- _data/publications.yml = [ {...}, {...} ] (array)
- _data/publications.yml = { publications: [ {...}, ... ] } (hash)
{%- endcomment -%}
{% assign pubs_raw = site.data.publications %}
{% assign pubs = pubs_raw.publications | default: pubs_raw %}

{%- comment -%}
Graceful empty state (no unsupported `{% exit %}`).
{%- endcomment -%}
{% if pubs == nil or pubs == empty or pubs.size == 0 %}
<p>No publications found. This page is driven by <code>_data/publications.yml</code>.</p>
{% else %}

{%- comment -%}
Sort newest first (year is numeric thanks to the workflow).
{%- endcomment -%}
{% assign pubs_sorted = pubs | sort: "year" | reverse %}

{%- comment -%}
Featured publications (selected_publication: true)
{%- endcomment -%}
{% assign featured = pubs_sorted | where: "selected_publication", true %}
{% if featured and featured.size > 0 %}
<h2 class="section-subtitle">Selected publications</h2>
<div class="pub-cards">
  {% for p in featured %}
  <article class="pub-card">
    {% if p.image %}
    <div class="pub-card-media">
      <img src="{{ p.image | relative_url }}" alt="{{ p.title | escape }}">
    </div>
    {% endif %}
    <div class="pub-card-body">
      <h3 class="pub-title">
        {% if p.url %}
          <a href="{{ p.url }}" target="_blank" rel="noopener">{{ p.title }}</a>
        {% else %}
          {{ p.title }}
        {% endif %}
      </h3>
      <div class="pub-meta">
        {% if p.authors %}{{ p.authors }} · {% endif %}
        {% if p.journal and p.url %}
          <a href="{{ p.url }}" target="_blank" rel="noopener">{{ p.journal }}</a>
        {% elsif p.journal %}
          {{ p.journal }}
        {% endif %}
        {% if p.year %} · {{ p.year }}{% endif %}
      </div>
    </div>
  </article>
  {% endfor %}
</div>
{% endif %}

{%- comment -%}
All publications grouped by year.
{%- endcomment -%}
<h2 class="section-subtitle">All publications</h2>

{%- assign pubs_with_year = pubs_sorted | where_exp: "p", "p.year" -%}
{%- assign groups = pubs_with_year | group_by: "year" -%}

{% for g in groups %}
  <h3 class="pub-year">{{ g.name }}</h3>
  <div class="pub-list">
    {% for p in g.items %}
      <div class="pub-list-item">
        <div class="pub-list-title">
          {% if p.url %}
            <a href="{{ p.url }}" target="_blank" rel="noopener">{{ p.title }}</a>
          {% else %}
            {{ p.title }}
          {% endif %}
        </div>
        <div class="pub-list-meta">
          {% if p.authors %}{{ p.authors }} · {% endif %}
          {% if p.journal and p.url %}
            <a href="{{ p.url }}" target="_blank" rel="noopener">{{ p.journal }}</a>
          {% elsif p.journal %}
            {{ p.journal }}
          {% endif %}
        </div>
      </div>
    {% endfor %}
  </div>
{% endfor %}

{% endif %}
