---
title: "People"
layout: default
permalink: /people/
---

<section class="people-page">
  <h1 class="page-title">Team members</h1>

  {% assign folks = site.data.people | default: empty %}
  <div class="people-list">
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
        {% if p.status %}<div class="person-status">{{ p.status }}</div>{% endif %}
        {% if p.bio %}<p class="person-bio">{{ p.bio }}</p>{% endif %}

        {% if p.github or p.scholar or p.linkedin %}
        <div class="person-social" aria-label="Profile links">
          {% if p.github %}
            <a href="{{ p.github }}" target="_blank" rel="noopener">
              <img class="icon" src="{{ '/assets/images/people/github.svg' | relative_url }}" alt="GitHub">
            </a>
          {% endif %}
          {% if p.scholar %}
            <a href="{{ p.scholar }}" target="_blank" rel="noopener">
              <img class="icon" src="{{ '/assets/images/people/scholar.svg' | relative_url }}" alt="Google Scholar">
            </a>
          {% endif %}
          {% if p.linkedin %}
            <a href="{{ p.linkedin }}" target="_blank" rel="noopener">
              <img class="icon" src="{{ '/assets/images/people/linkedin.svg' | relative_url }}" alt="LinkedIn">
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
