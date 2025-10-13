---
title: Publications
layout: default
permalink: /publications/
---

{% comment %}
Entries in _data/publications.yml should be of the form
- title:
  authors:
  journal:
  year: 2025
  url: https://...
  image: /assets/images/pubs/foo.png   # optional (only shown for Selected Publications)
  selected-publication: yes            # yes or no
{% endcomment %}

{% assign pubs_all = site.data.publications | sort: "year" | reverse %}

{% assign selected = pubs_all
  | where_exp: "p", 'p["selected-publication"] == true or p["selected-publication"] == "yes"'
%}

# Selected publications

<div class="pub-grid">
  {% for p in selected %}
  <article class="pub-card has-media">
    {% if p.image %}
      <div class="pub-thumb">
        <img src="{{ p.image | relative_url }}" alt="{{ p.title | escape }}">
      </div>
    {% endif %}

    <div class="pub-body">
      <h3 class="pub-title">{{ p.title }}</h3>
      {% if p.authors %}<div class="pub-authors">{{ p.authors }}</div>{% endif %}
      <div class="pub-meta">
        {% if p.url and p.journal %}
          <em class="pub-journal">
            <a href="{{ p.url }}" target="_blank" rel="noopener">{{ p.journal }}</a>
          </em>
        {% elsif p.journal %}
          <em class="pub-journal">{{ p.journal }}</em>
        {% endif %}
        {% if p.year %}<span class="pub-year">({{ p.year }})</span>{% endif %}
      </div>
    </div>
  </article>
  {% endfor %}
</div>

---

# Full list

{% assign years = pubs_all | map: "year" | uniq | sort | reverse %}
{% for y in years %}
  <h3 class="pub-year-heading">{{ y }}</h3>
  <div class="pub-list">
    {% assign pubs_year = pubs_all | where: "year", y %}
    {% for p in pubs_year %}
      <article class="pub-card">
        <div class="pub-body">
          <h4 class="pub-title">{{ p.title }}</h4>
          {% if p.authors %}<div class="pub-authors">{{ p.authors }}</div>{% endif %}
          <div class="pub-meta">
            {% if p.url and p.journal %}
              <em class="pub-journal">
                <a href="{{ p.url }}" target="_blank" rel="noopener">{{ p.journal }}</a>
              </em>
            {% elsif p.journal %}
              <em class="pub-journal">{{ p.journal }}</em>
            {% endif %}
            {% if p.year %}<span class="pub-year">({{ p.year }})</span>{% endif %}
          </div>
        </div>
      </article>
    {% endfor %}
  </div>
{% endfor %}
