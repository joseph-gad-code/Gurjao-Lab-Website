---
title: "People"
layout: default
permalink: /people/
---

<section class="people-page">
  <h1 class="page-title">Team members</h1>

  <div class="people-list">
    {% assign folks = site.data.people %}
    {% for p in folks %}
    <article class="person-card">
      <div class="person-photo-wrap">
        {% if p.image %}
          <img class="person-photo" src="{{ p.image | relative_url }}" alt="{{ p.name }}">
        {% else %}
          <div class="person-photo placeholder" aria-hidden="true">Image</div>
        {% endif %}
      </div>

      <div class="person-meta">
        <h3 class="person-name">{{ p.name }}</h3>
        <div class="person-role">{{ p.role | default: p.status }}</div>
        {% if p.bio %}<p class="person-bio">{{ p.bio }}</p>{% endif %}

        {% if p.github or p.scholar or p.linkedin %}
        <div class="person-social" aria-label="Profile links">
          {% if p.github %}
            <a href="{{ p.github }}" target="_blank" rel="noopener" title="GitHub" aria-label="GitHub">
              <svg viewBox="0 0 24 24" class="icon"><path d="M12 .5a12 12 0 0 0-3.8 23.4c.6.1.8-.2.8-.6v-2c-3.4.7-4.1-1.6-4.1-1.6-.6-1.5-1.5-1.9-1.5-1.9-1.3-.9.1-.9.1-.9 1.5.1 2.2 1.6 2.2 1.6 1.3 2.2 3.5 1.6 4.3 1.2.1-1 .5-1.6.9-2-2.7-.3-5.6-1.4-5.6-6.2 0-1.4.5-2.5 1.3-3.4-.1-.3-.6-1.7.1-3.6 0 0 1.1-.3 3.6 1.3 1-.3 2-.4 3-.4s2 .1 3 .4c2.5-1.6 3.6-1.3 3.6-1.3.7 1.9.2 3.3.1 3.6.9.9 1.3 2 1.3 3.4 0 4.8-2.9 5.9-5.6 6.2.5.4.9 1.2.9 2.5v3.7c0 .4.2.7.8.6A12 12 0 0 0 12 .5Z"/></svg>
            </a>
          {% endif %}

          {% if p.scholar %}
            <a href="{{ p.scholar }}" target="_blank" rel="noopener" title="Google Scholar" aria-label="Google Scholar">
              <svg viewBox="0 0 24 24" class="icon"><path d="M12 3 2 9l10 6 6-3.6V18h4V9L12 3z"/></svg>
            </a>
          {% endif %}

          {% if p.linkedin %}
            <a href="{{ p.linkedin }}" target="_blank" rel="noopener" title="LinkedIn" aria-label="LinkedIn">
              <svg viewBox="0 0 24 24" class="icon"><path d="M4.98 3.5a2.5 2.5 0 1 1 0 5.001 2.5 2.5 0 0 1 0-5zM3 9h4v12H3zM14.5 9c-3.1 0-4.5 1.7-4.5 3.7V21h4v-6.1c0-1 .7-1.9 2-1.9s2 1 2 2V21h4v-6.9C22 10.6 20 9 17.5 9c-1.2 0-2.5.5-3 1.4V9h0z"/></svg>
            </a>
          {% endif %}
        </div>
        {% endif %}
      </div>
    </article>
    {% endfor %}
  </div>
</section>

<section class="values-section">
  <h2 class="page-title">Core values</h2>

  <div class="values-grid">
    <div class="value-col">
      <h3>Lab community</h3>
      <p>
        The Gurjao Lab aims to be a vibrant home for curiosity and collaboration.
        Our members come from diverse backgrounds, bringing together expertise
        across disciplines to tackle fundamental and applied questions in cancer
        research. Lab members are trusted to take ownership of their science
        while being supported by peers and mentors. Outside of the lab, we
        contribute by the creation of a postdoc mentorship committee at IRIC.
      </p>
    </div>

    <div class="value-col">
      <h3>DEI commitment</h3>
      <p>
        We celebrate diversity as a source of strength and innovation in our work.
        We are committed to an inclusive, equitable, and welcoming environment
        for all members. We participate in EDI initiatives at IRIC and pursue
        research for equitable access to cancer care across demographics.
      </p>
    </div>
  </div>
</section>
