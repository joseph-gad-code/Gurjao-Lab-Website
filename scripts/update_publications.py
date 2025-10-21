<h1>All publications</h1>

{%- assign _empty = "" | split: "" -%}
{%- assign pubs = site.data.publications | default: _empty -%}
{%- assign all_sorted = pubs | sort: "year" | reverse -%}

/* Build a flat list of unique year strings (handles year: 2020 and year: [2020]) */
{%- assign years = "" | split: "" -%}
{%- for p in all_sorted -%}
  {%- comment -%}Normalize to a string{%- endcomment -%}
  {%- capture _py -%}{% if p.year and p.year.first %}{{ p.year.first }}{% else %}{{ p.year }}{% endif %}{%- endcapture -%}
  {%- assign _py = _py | strip -%}
  {%- if _py != "" and years contains _py == false -%}
    {%- assign years = years | push: _py -%}
  {%- endif -%}
{%- endfor -%}
{%- assign years = years | sort | reverse -%}

{%- for y in years -%}
  <div class="pub-year-header">{{ y }}</div>

  {%- comment -%}
    Pick pubs for this year, accepting either p.year == y or p.year[0] == y
  {%- endcomment -%}
  {%- assign pubs_for_year = all_sorted 
      | where_exp: "p", "p.year == y or (p.year and p.year[0] == y)" -%}

  <div class="pub-list">
    {%- for p in pubs_for_year -%}
      {%- capture authors -%}
        {% include authors_compact.html authors=p.authors max=10 highlight_list=page.lab_names %}
      {%- endcapture -%}

      <article class="pub-row">
        <h3 class="title">
          {%- assign _doi = p.doi | default: "" | strip -%}
          {%- if _doi != "" -%}
            <a href="https://doi.org/{{ _doi }}" target="_blank" rel="noopener">{{ p.title }}</a>
          {%- elsif p.url -%}
            <a href="{{ p.url }}" target="_blank" rel="noopener">{{ p.title }}</a>
          {%- else -%}
            {{ p.title }}
          {%- endif -%}
        </h3>

        {%- if p.authors -%}
          <div class="authors">{{ authors | strip }}</div>
        {%- endif -%}

        <div class="venue">
          {%- if p.journal -%}<em>{{ p.journal }}</em>{%- endif -%}
          {%- if p.volume and p.volume != "" -%}, {{ p.volume }}{%- endif -%}
          {%- if p.issue and p.issue != "" -%}({{ p.issue }}){%- endif -%}
          {%- if p.pages and p.pages != "" -%}, {{ p.pages }}{%- endif -%}
          {%- if y and y != "" -%}<span class="year">, {{ y }}</span>{%- endif -%}
          {%- if _doi != "" -%}
            <a class="doi" href="https://doi.org/{{ _doi }}" target="_blank" rel="noopener">DOI</a>
          {%- endif -%}
        </div>
      </article>
    {%- endfor -%}
  </div>
{%- endfor -%}
