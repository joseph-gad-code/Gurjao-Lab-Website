{%- assign p = include.p -%}
<article class="pub-card">
  {%- if p.image -%}
    <div class="pub-card-media">
      {%- if p.url -%}
        <a href="{{ p.url }}" target="_blank" rel="noopener">
          <img src="{{ p.image | relative_url }}" alt="{{ p.title | escape }}">
        </a>
      {%- else -%}
        <img src="{{ p.image | relative_url }}" alt="{{ p.title | escape }}">
      {%- endif -%}
    </div>
  {%- endif -%}

  <div class="pub-card-body">
    <h4 class="pub-card-title">
      {%- if p.url -%}
        <a href="{{ p.url }}" target="_blank" rel="noopener">{{ p.title }}</a>
      {%- else -%}
        {{ p.title }}
      {%- endif -%}
    </h4>
    <div class="pub-card-meta">
      <span class="pub-card-authors">{{ p.authors }}</span>
      {%- if p.journal -%}
        &nbsp;—&nbsp;<span class="pub-card-journal">{{ p.journal }}</span>
      {%- endif -%}
      {%- if p.year -%}
        <span class="pub-card-year">({{ p.year }})</span>
      {%- endif -%}
    </div>
  </div>
</article>
