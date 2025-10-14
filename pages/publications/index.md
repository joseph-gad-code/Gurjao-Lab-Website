---
title: "Publications"
layout: default
permalink: /publications/
---

{%- comment -%}
Normalize the data source to an array called `all`.
We support either:
- _data/publications.yml with a `publications:` root key
- _data/publications.yml being a bare array (less preferred, but guarded)
{%- endcomment -%}
{% assign pub_root = site.data.publications %}
{% assign all_from_key = pub_root.publications %}
{% if all_from_key %}
  {% assign all = all_from_key %}
{% else %}
  {% assign all = pub_root %}
{% endif %}
{% if all == nil %}
  {% assign all = "" | split:"|" %}
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
    {%- assign all_sorted = all | sort: "year" | reverse -%}
    {%- assign grouped = all_sorted | group_by: "year" -%}
    {%- assign groups_sorted = grouped | sort: "name" | reverse -%}

    {%- for g in groups_sorted -%}
      <h3 class="pubs-year">{{ g.name }}</h3>
      <div class="pubs-list">
        {%- for p in g.items -%}
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
        {%- endfor -%}
      </div>
    {%- endfor -%}
  {% else %}
    <p>No publications found yet.</p>
  {% endif %}
</section>
