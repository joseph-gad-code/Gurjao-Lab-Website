---
title: "Publications"
layout: default
permalink: /publications/
lab_names:
  - Gurjao
  - Boero-Teyssier
  - Hooper
  - Gad
---

<section class="pubs">

  <h1>Selected publications</h1>

  {% assign selected = site.data.publications | where: "selected_publication", true %}
  {% if selected and selected.size > 0 %}
  <div class="pub-grid">
    {% for p in selected %}

      {% assign raw_j = p.journal_clean | default: p.journal | default: "" | strip %}
      {% assign basic = raw_j | split:"(" | first | split: "," | first | strip %}
      {% assign toks  = basic | split:" " %}
      {% assign last_tok = toks | last | replace:".","" | replace:",","" | strip %}
      {% assign last_is_number = "no" %}
      {% for d in (0..9) %}{% if last_tok contains d %}{% assign last_is_number = "yes" %}{% endif %}{% endfor %}
      {% capture journal_clean %}
        {% for t in toks %}
          {% if forloop.last and last_is_number == "yes" %}{% break %}{% endif %}{{ t }}{% unless forloop.last %} {% endunless %}
        {% endfor %}
      {% endcapture %}
      {% assign journal_clean = journal_clean | strip %}

      {% assign authors = p.authors | replace:"*","" | replace:"...", "…" %}
      {% for ln in page.lab_names %}
        {% assign needle1 = " " | append: ln %}
        {% assign repl1   = " <strong>" | append: ln | append: "</strong>" %}
        {% assign authors = authors | replace: needle1, repl1 %}
        {% assign needle2 = ln | append: "," %}
        {% assign repl2   = "<strong>" | append: ln | append: "</strong>," %}
        {% assign authors = authors | replace: needle2, repl2 %}
      {% endfor %}

      <article class="pub-card">
        <a class="thumb" href="{{ p.url }}" target="_blank" rel="noopener">
          {% if p.image %}
            <img src="{{ p.image | relative_url }}" alt="{{ p.title | escape }}">
          {% else %}
            <div class="thumb-fallback" aria-hidden="true">No image</div>
          {% endif %}
        </a>

        <div class="meta">
          <h3 class="title">
            <a class="title-link" href="{{ p.url }}" target="_blank" rel="noopener">{{ p.title }}</a>
          </h3>

          {% if p.authors %}
            <div class="authors">{{ authors }}</div>
          {% endif %}

          <div class="venue">
            {% if journal_clean != "" -%}
              <em><a href="{{ p.url }}" target="_blank" rel="noopener">{{ journal_clean }}</a></em>
            {%- endif -%}
            {%- if p.year -%}<span class="year">, {{ p.year }}</span>{%- endif -%}
            {% if p.doi and p.doi != "" %} <a class="doi" href="https://doi.org/{{ p.doi }}" target="_blank" rel="noopener">DOI</a>{% endif %}
          </div>
        </div>
      </article>
    {% endfor %}
  </div>
  {% else %}
    <p>No selected publications yet.</p>
  {% endif %}

  <h1>All publications</h1>

  {% assign all_sorted = site.data.publications | sort: "year" | reverse %}
  <div class="pub-list">
    {% for p in all_sorted %}

      {% assign raw_j = p.journal_clean | default: p.journal | default: "" | strip %}
      {% assign basic = raw_j | split:"(" | first | split: "," | first | strip %}
      {% assign toks  = basic | split:" " %}
      {% assign last_tok = toks | last | replace:".","" | replace:",","" | strip %}
      {% assign last_is_number = "no" %}
      {% for d in (0..9) %}{% if last_tok contains d %}{% assign last_is_number = "yes" %}{% endif %}{% endfor %}
      {% capture journal_clean %}
        {% for t in toks %}
          {% if forloop.last and last_is_number == "yes" %}{% break %}{% endif %}{{ t }}{% unless forloop.last %} {% endunless %}
        {% endfor %}
      {% endcapture %}
      {% assign journal_clean = journal_clean | strip %}

      {% assign authors = p.authors | replace:"*","" | replace:"...", "…" %}
      {% for ln in page.lab_names %}
        {% assign needle1 = " " | append: ln %}
        {% assign repl1   = " <strong>" | append: ln | append: "</strong>" %}
        {% assign authors = authors | replace: needle1, repl1 %}
        {% assign needle2 = ln | append: "," %}
        {% assign repl2   = "<strong>" | append: ln | append: "</strong>," %}
        {% assign authors = authors | replace: needle2, repl2 %}
      {% endfor %}

      <article class="pub-row">
        <h3 class="title">
          <a class="title-link" href="{{ p.url }}" target="_blank" rel="noopener">{{ p.title }}</a>
        </h3>
        {% if p.authors %}
          <div class="authors">{{ authors }}</div>
        {% endif %}
        <div class="venue">
          {% if journal_clean != "" -%}
            <em><a href="{{ p.url }}" target="_blank" rel="noopener">{{ journal_clean }}</a></em>
          {%- endif -%}
          {%- if p.year -%}<span class="year">, {{ p.year }}</span>{%- endif -%}
          {% if p.doi and p.doi != "" %} <a class="doi" href="https://doi.org/{{ p.doi }}" target="_blank" rel="noopener">DOI</a>{% endif %}
        </div>
      </article>
    {% endfor %}
  </div>
</section>
