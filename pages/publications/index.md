---
title: "Publications"
layout: default
permalink: /publications/
---

<section class="pubs-page">
  <h1>Publications</h1>

  {%- assign pubs = site.data.publications | default: empty -%}

  {%- if pubs == empty or pubs == nil or pubs.size == 0 -%}
    <p>No publications found yet.</p>
  {%- else -%}

    {%- assign selected = pubs | where: "selected_publication", true -%}
    {%- assign not_selected = pubs | where_exp: "x", "x.selected_publication != true" -%}

    {%- if selected and selected.size > 0 -%}
      <h2 class="pubs-subtitle">Selected publications</h2>
      <div class="pub-cards-grid">
        {%- for p in selected -%}
          {%- assign clean_authors = p.authors
              | replace: ', ...', ''
              | replace: '...', ''
              | replace: '*', '' -%}
          <article class="pub-card">
            {%- if p.image and p.image != "" -%}
              <div class="pub-card-media">
                <img src="{{ p.image | relative_url }}" alt="{{ p.title | escape }}">
              </div>
            {%- endif -%}
            <div class="pub-card-body">
              <h3 class="pub-title">
                <a class="pub-link" href="{{ p.url }}" target="_blank" rel="noopener">{{ p.title }}</a>
              </h3>
              <div class="pub-authors">{{ clean_authors }}</div>
              <div class="pub-venue">
                <em>
                  <a class="pub-link" href="{{ p.url }}" target="_blank" rel="noopener">{{ p.journal }}</a>
                </em>
                {%- unless p.journal contains p.year -%}
                  <span class="pub-year"> · {{ p.year }}</span>
                {%- endunless -%}
              </div>
              {%- if p.doi and p.doi != "" -%}
                <div class="pub-actions">
                  <a class="pub-btn" href="https://doi.org/{{ p.doi }}" target="_blank" rel="noopener">DOI</a>
                </div>
              {%- endif -%}
            </div>
          </article>
        {%- endfor -%}
      </div>
    {%- endif -%}

    <h2 class="pubs-subtitle">All publications</h2>
    {%- assign years = pubs | map: "year" | uniq | sort | reverse -%}

    {%- for y in years -%}
      <h3 class="pub-year-heading">{{ y }}</h3>
      <div class="pub-list">
        {%- for p in not_selected -%}
          {%- if p.year == y -%}
            {%- assign clean_authors = p.authors
                | replace: ', ...', ''
                | replace: '...', ''
                | replace: '*', '' -%}
            <article class="pub-list-item">
              <h4 class="pub-title">
                <a class="pub-link" href="{{ p.url }}" target="_blank" rel="noopener">{{ p.title }}</a>
              </h4>
              <div class="pub-authors">{{ clean_authors }}</div>
              <div class="pub-venue">
                <em>
                  <a class="pub-link" href="{{ p.url }}" target="_blank" rel="noopener">{{ p.journal }}</a>
                </em>
                {%- unless p.journal contains p.year -%}
                  <span class="pub-year"> · {{ p.year }}</span>
                {%- endunless -%}
              </div>
              {%- if p.doi and p.doi != "" -%}
                <div class="pub-actions">
                  <a class="pub-btn" href="https://doi.org/{{ p.doi }}" target="_blank" rel="noopener">DOI</a>
                </div>
              {%- endif -%}
            </article>
          {%- endif -%}
        {%- endfor -%}
      </div>
    {%- endfor -%}

  {%- endif -%}
</section>
