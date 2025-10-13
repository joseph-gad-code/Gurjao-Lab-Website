---
title: Publications
layout: default
permalink: /publications/
---

<section class="pubs">
  <h2>Selected publications</h2>

  {% assign pubs_all = site.data.publications | sort: "year" | reverse %}
  {% assign pubs_selected = pubs_all | where_exp: "p", "p['selected-publication'] == true" %}

  <div class="pubs-grid">
    {% for p in pubs_selected %}
      <article class="pub-card">
        {% if p.image %}
          <a class="pub-thumb" href="{{ p.url | default: p.journal_url | default: '#' }}" target="_blank" rel="noopener">
            <img loading="lazy" src="{{ p.image | relative_url }}" alt="{{ p.title | escape }}">
          </a>
        {% endif %}

        <div class="pub-body">
          <h3 class="pub-title">
            {% if p.url %}
              <a href="{{ p.url }}" target="_blank" rel="noopener">{{ p.title }}</a>
            {% else %}
              {{ p.title }}
            {% endif %}
          </h3>

          <div class="pub-authors">
            {% include authors_bold.html text=p.authors %}
          </div>

          <div class="pub-meta">
            {% if p.journal_url %}
              <a href="{{ p.journal_url }}" target="_blank" rel="noopener">{{ p.journal }}</a>
            {% else %}
              {{ p.journal }}
            {% endif %}
            {% if p.year %} • {{ p.year }}{% endif %}
          </div>
        </div>
      </article>
    {% endfor %}
  </div>
</section>

<section class="pubs-all">
  <h2>Full list</h2>

  {% assign groups = pubs_all | group_by: "year" %}
  {% assign groups = groups | sort: "name" | reverse %}

  {% for g in groups %}
    <h3 class="pub-year">{{ g.name }}</h3>
    <div class="pubs-list">
      {% for p in g.items %}
        <article class="pub-line">
          <h4 class="pub-title">
            {% if p.url %}
              <a href="{{ p.url }}" target="_blank" rel="noopener">{{ p.title }}</a>
            {% else %}
              {{ p.title }}
            {% endif %}
          </h4>

          <div class="pub-authors">
            {% include authors_bold.html text=p.authors %}
          </div>

          <div class="pub-meta">
            {% if p.journal_url %}
              <a href="{{ p.journal_url }}" target="_blank" rel="noopener">{{ p.journal }}</a>
            {% else %}
              {{ p.journal }}
            {% endif %}
            {% if p.volume %} {{ p.volume }}{% endif %}
            {% if p.pages %} , {{ p.pages }}{% endif %}
            {% if p.year %} • {{ p.year }}{% endif %}
          </div>
        </article>
      {% endfor %}
    </div>
  {% endfor %}
</section>
