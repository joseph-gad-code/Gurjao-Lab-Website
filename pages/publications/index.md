---
title: "Publications"
layout: default
permalink: /publications/
---

# Publications

{%- comment -%}
Load data.
Accept either:
- _data/publications.yml = [ {...}, {...} ] (array)
- _data/publications.yml = { publications: [ {...}, ... ] } (hash)
{%- endcomment -%}
{% assign pubs_raw = site.data.publications %}
{% assign pubs = pubs_raw.publications | default: pubs_raw %}

{%- comment -%}
Empty state.
{%- endcomment -%}
{% if pubs == nil or pubs == empty or pubs.size == 0 %}
<p>No publications found. This page is driven by <code>_data/publications.yml</code>.</p>
{% else %}

{%- comment -%}
Sort newest first if possible. If items aren’t hashes, sort will still pass through.
{%- endcomment -%}
{% assign pubs_sorted = pubs | sort: "year" | reverse %}

{%- comment -%}
Featured publications (selected_publication: true). We’ll detect the flag inside the loop
to avoid filters that assume every item is a hash.
{%- endcomment -%}
{% assign any_featured = false %}
{% for p in pubs_sorted %}
  {% if p and p.selected_publication %}
    {% assign any_featured = true %}
    {% break %}
  {% endif %}
{% endfor %}

{% if any_featured %}
<h2 class="section-subtitle">Selected publications</h2>
<div class="pub-cards">
  {% for p in pubs_sorted %}
    {% if p and p.selected_publication %}
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
    {% endif %}
  {% endfor %}
</div>
{% endif %}

{%- comment -%}
All publications (no grouping; avoids map/where_exp/group_by).
We’ll just render in sorted order and skip any non-hash items.
{%- endcomment -%}
<h2 class="section-subtitle">All publications</h2>
<div class="pub-list">
  {% assign any_items = false %}
  {% for p in pubs_sorted %}
    {% if p and p.title %}
      {% assign any_items = true %}
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
          {% if p.year %} · {{ p.year }}{% endif %}
        </div>
      </div>
    {% endif %}
  {% endfor %}

  {% unless any_items %}
    <p>No well-formed publication entries to display.</p>
  {% endunless %}
</div>

{% endif %}
