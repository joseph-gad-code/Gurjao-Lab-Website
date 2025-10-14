---
title: "Publications"
layout: default
permalink: /publications/
---

{% comment %}
Normalize data:
- Accept either `_data/publications.yml` = [ {...}, {...} ]  (array)
- Or `_data/publications.yml` = { publications: [ {...}, ... ] } (hash)
{% endcomment %}
{% assign pubs_raw = site.data.publications %}
{% if pubs_raw == nil %}
  <p>No publications data found. Make sure <code>_data/publications.yml</code> exists.</p>
  {% exit %}
{% endif %}

{% assign pubs =
  pubs_raw.publications | default: pubs_raw
%}

{%- comment -%}
Ensure we have an array of hashes
{%- endcomment -%}
{% unless pubs.size %}
  <p>No publications available yet.</p>
  {% exit %}
{% endunless %}

{%- comment -%}
Coerce/clean: ensure year is present, build a safe link, and default booleans
{%- endcomment -%}
{% assign cleaned = "" | split: "" %}
{% for p in pubs %}
  {% assign year = p.year | default: p.issued | default: "" %}
  {% if year != "" %}
    {% assign year_num = year | plus: 0 %}
  {% else %}
    {% assign year_num = 0 %}
  {% endif %}

  {% assign has_doi = p.doi | default: "" %}
  {% assign url = p.url | default: "" %}
  {% if url == "" and has_doi != "" %}
    {% assign url = "https://doi.org/" | append: has_doi %}
  {% endif %}

  {% assign selected_flag = p.selected_publication | default: false %}

  {% assign item = p | merge: 
      {
        "year": year_num,
        "url": url,
        "selected_publication": selected_flag
      }
  %}
  {% assign cleaned = cleaned | push: item %}
{% endfor %}

{%- comment -%}
Sort newest first
{%- endcomment -%}
{% assign pubs_sorted = cleaned | sort: "year" | reverse %}

<h1>Publications</h1>

{%- comment -%}
Selected publications (cards, 2 columns)
Mark a publication selected by setting `selected_publication: true` in YAML.
Optionally add `image: /path/to/img.jpg`.
{%- endcomment -%}
{% assign featured = pubs_sorted | where: "selected_publication", true %}
{% if featured.size > 0 %}
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
            {% if p.year and p.year != 0 %} · {{ p.year }}{% endif %}
          </div>
        </div>
      </article>
    {% endfor %}
  </div>
{% endif %}

{%- comment -%}
All publications grouped by year (not numbered)
{%- endcomment -%}
<h2 class="section-subtitle">All publications</h2>
{% assign pubs_with_year = pubs_sorted | where_exp: "p", "p.year and p.year != 0" %}
{% assign groups = pubs_with_year | group_by: "year" %}

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
