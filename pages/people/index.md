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
        <div class="person-role">{{ p.status }}</div>
        {% if p.bio %}<p class="person-bio">{{ p.bio }}</p>{% endif %}

        {% if p.github or p.scholar or p.linkedin %}
        <div class="person-social" aria-label="Profile links">
          {% if p.github %}
            <a href="{{ p.github }}" target="_blank" rel="noopener" title="GitHub" aria-label="GitHub">
              <img class="icon" src="{{ '/assets/images/people/github.svg' | relative_url }}" alt="GitHub icon">
            </a>
          {% endif %}
          {% if p.scholar %}
            <a href="{{ p.scholar }}" target="_blank" rel="noopener" title="Google Scholar" aria-label="Google Scholar">
              <img class="icon" src="{{ '/assets/images/people/scholar.svg' | relative_url }}" alt="Google Scholar icon">
            </a>
          {% endif %}
          {% if p.linkedin %}
            <a href="{{ p.linkedin }}" target="_blank" rel="noopener" title="LinkedIn" aria-label="LinkedIn">
              <img class="icon" src="{{ '/assets/images/people/linkedin.svg' | relative_url }}" alt="LinkedIn icon">
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

