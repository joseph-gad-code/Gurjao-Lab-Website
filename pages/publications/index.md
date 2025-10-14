---
title: "Publications"
layout: default
permalink: /publications/
---

{% comment %}
Safely load the publications array from _data/publications.yml.
Supports either:
- publications.yml with a top-level "publications" array, or
- publications.yml that IS the array.
{% endcomment %}
{% assign pub_root = site.data.publications %}
{% assign all_raw = pub_root.publications | default: pub_root %}
{% if all_raw == nil or all_raw == empty %}
  {% assign all = "" | split:"|" %} {# empty array #}
{% else %}
  {% assign all = all_raw %}
{% endif %}

<section class="pubs">
  <h2>Selected publications</h2>

  {% assign featured = all | where: "selected_publication", true %}
  {% if featured and featured.size > 0 %}
    {% assign featured_sorted = featured | sort: "year" | reverse %}
    <div class="pubs-grid">
      {% for p in featured_sorted %}
        {% include pub-card.html p=p %}
      {% endfor %}
    </div>
  {% else %}
    <p>No selected publications yet.</p>
  {% endif %}

  <hr class="pubs-divider">

  <h2>All publications</h2>

  {% if all and all.size > 0 %}
    {% assign sorted = all | sort: "year" | reverse %}

    {%- assign years = "" | split:"|" -%}
    {%- for item in sorted -%}
      {%- unless years contains item.year -%}
        {%- assign years = years | push: item.year -%}
      {%- endunless -%}
    {%- endfor -%}

    {%- for y in years -%}
      <h3 class="pubs-year">{{ y }}</h3>
      <div class="pubs-list">
        {%- for p in sorted -%}
          {%- if p.year == y -%}
            <article class="pubs-item">
              <h4 class="pubs-title">
                {%- if p.url -%}<a href="{{ p.url }}" target="_blank" rel="noopener">{%- endif -%}
                {{ p.title }}
                {%- if p.url -%}</a>{%- endif -%}
              </h4>
              <div class="pubs-meta">
                <span class="pubs-authors">{{ p.authors }}</span>
                {%- if p.journal -%}
                  &nbsp;—&nbsp;
                  {%- if p.url -%}
                    <a class="pubs-journal" href="{{ p.url }}" target="_blank" rel="noopener">{{ p.journal }}</a>
                  {%- else -%}
                    <span class="pubs-journal">{{ p.journal }}</span>
                  {%- endif -%}
                {%- endif -%}
                {%- if p.year -%} <span>({{ p.year }})</span>{%- endif -%}
              </div>
            </article>
          {%- endif -%}
        {%- endfor -%}
      </div>
    {%- endfor -%}
  {% else %}
    <p>No publications found yet.</p>
  {% endif %}
</section>
