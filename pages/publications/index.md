---
title: "Publications"
layout: default
permalink: /publications/
---

{%- comment -%}
Helpers
- lab_last_names: last names from _data/people.yml (for bolding)
- selected: subset where selected_publication == true
- all_pubs: all publications sorted by year desc, then title
{%- endcomment -%}

{%- assign people = site.data.people | default: empty -%}
{%- assign lab_last_names = "" -%}
{%- if people and people.size > 0 -%}
  {%- capture lab_last_names -%}
    {%- for p in people -%}
      {%- assign last = p.name | split: " " | last -%}
      {{ last }}{% unless forloop.last %}|{% endunless %}
    {%- endfor -%}
  {%- endcapture -%}
{%- endif -%}

{%- assign pubs = site.data.publications | default: empty -%}
{%- assign selected = pubs | where_exp: "p", "p.selected_publication" -%}

{%- comment -%}
Sort all publications: newest first (year desc), then title
{%- endcomment -%}
{%- assign all_sorted = pubs | sort: "title" -%}
{%- assign years = "" -%}
{%- assign all_sorted = all_sorted | sort: "year" | reverse -%}

# Selected publications

{%- if selected and selected.size > 0 -%}
<div class="pub-grid">
  {%- for p in selected -%}
    <article class="pub-card">
      {%- if p.image and p.image != "" -%}
        <a class="pub-thumb" href="{{ p.url }}" target="_blank" rel="noopener">
          <img loading="lazy" src="{{ p.image | relative_url }}" alt="{{ p.title | escape }}">
        </a>
      {%- endif -%}

      <div class="pub-info">
        <h3 class="pub-title">
          <a href="{{ p.url }}" target="_blank" rel="noopener">{{ p.title }}</a>
        </h3>

        {%- assign raw_authors = p.authors | default: "" -%}
        {%- assign list = raw_authors | split: ", " -%}

        {%- comment -%}
        Build an authors line:
        - Bold lab members (match last name against lab_last_names regex)
        - Limit to 12 authors; append "…" if trimmed, but keep any lab names even if beyond 12 (they’ll be included)
        {%- endcomment -%}
        {%- assign max_display = 12 -%}
        {%- capture authors_line -%}
          {%- assign shown = 0 -%}
          {%- assign printed = 0 -%}
          {%- for a in list -%}
            {%- assign last = a | strip | split: " " | last -%}
            {%- assign is_lab = false -%}
            {%- if lab_last_names and last != "" and lab_last_names contains last -%}
              {%- assign is_lab = true -%}
            {%- endif -%}

            {%- if shown < max_display or is_lab -%}
              {%- if printed > 0 %}, {% endif -%}
              {%- if is_lab -%}<strong>{{ a | replace: "*", "" }}</strong>{%- else -%}{{ a | replace: "*", "" }}{%- endif -%}
              {%- assign printed = printed | plus: 1 -%}
            {%- endif -%}

            {%- assign shown = shown | plus: 1 -%}
          {%- endfor -%}
          {%- if list.size > printed -%}…{%- endif -%}
        {%- endcapture -%}

        <div class="pub-authors">{{ authors_line | strip }}</div>

        {%- comment -%}
        Journal, linked to scholar page, only the name (strip everything after first comma)
        {%- endcomment -%}
        {%- assign jname = p.journal | default: "" -%}
        {%- assign jdisplay = jname | split: "," | first | strip -%}
        <div class="pub-meta">
          <em><a href="{{ p.url }}" target="_blank" rel="noopener">{{ jdisplay }}</a></em>
          {%- if p.year %}, {{ p.year }}{%- endif -%}
          {%- if p.doi and p.doi != "" -%}
            &nbsp;·&nbsp;<a class="pub-doi" href="https://doi.org/{{ p.doi }}" target="_blank" rel="noopener">DOI</a>
          {%- endif -%}
        </div>
      </div>
    </article>
  {%- endfor -%}
</div>
{%- else -%}
<p>No selected publications yet.</p>
{%- endif -%}


# All publications

{%- comment -%}
Group by year (desc), reusing all_sorted which is sorted by year desc already.
{%- endcomment -%}
{%- assign years_seen = "" -%}
{%- for p in all_sorted -%}
  {%- assign y = p.year | default: "Other" -%}
  {%- unless years_seen contains y -%}
  {%- if forloop.index > 1 -%}</section>{%- endif -%}
  <section class="pub-year">
    <h2 class="pub-year-title">{{ y }}</h2>
  {%- capture years_seen -%}{{ years_seen }}|{{ y }}{%- endcapture -%}
  {%- endunless -%}

  <article class="pub-row">
    <h3 class="pub-title-sm">
      <a href="{{ p.url }}" target="_blank" rel="noopener">{{ p.title }}</a>
    </h3>

    {%- assign raw_authors = p.authors | default: "" -%}
    {%- assign list = raw_authors | split: ", " -%}
    {%- assign max_display = 18 -%}
    {%- capture authors_line -%}
      {%- assign shown = 0 -%}
      {%- assign printed = 0 -%}
      {%- for a in list -%}
        {%- assign last = a | strip | split: " " | last -%}
        {%- assign is_lab = false -%}
        {%- if lab_last_names and last != "" and lab_last_names contains last -%}
          {%- assign is_lab = true -%}
        {%- endif -%}

        {%- if shown < max_display or is_lab -%}
          {%- if printed > 0 %}, {% endif -%}
          {%- if is_lab -%}<strong>{{ a | replace: "*", "" }}</strong>{%- else -%}{{ a | replace: "*", "" }}{%- endif -%}
          {%- assign printed = printed | plus: 1 -%}
        {%- endif -%}
        {%- assign shown = shown | plus: 1 -%}
      {%- endfor -%}
      {%- if list.size > printed -%}…{%- endif -%}
    {%- endcapture -%}
    <div class="pub-authors-sm">{{ authors_line | strip }}</div>

    {%- assign jname = p.journal | default: "" -%}
    {%- assign jdisplay = jname | split: "," | first | strip -%}
    <div class="pub-meta-sm">
      <em><a href="{{ p.url }}" target="_blank" rel="noopener">{{ jdisplay }}</a></em>
      {%- if p.year %}, {{ p.year }}{%- endif -%}
      {%- if p.doi and p.doi != "" -%}
        &nbsp;·&nbsp;<a class="pub-doi" href="https://doi.org/{{ p.doi }}" target="_blank" rel="noopener">DOI</a>
      {%- endif -%}
    </div>
  </article>

  {%- if forloop.last -%}</section>{%- endif -%}
{%- endfor -%}
