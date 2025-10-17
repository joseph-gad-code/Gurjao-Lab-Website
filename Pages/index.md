---
title: "Home"
layout: default
permalink: /
---

<section class="home-hero container">
  <div class="media">
    <!-- Replace /assets/images/hero/hero.jpg with your file -->
    <img src="{{ '/assets/images/hero/hero.jpg' | relative_url }}" alt="Lab hero image">
  </div>
</section>

<section class="home-tagline container">
  <h1 class="t-display">We study cancer genomes for<br><span class="t-bold t-brand">Prevention</span> and <span class="t-bold t-brand">Treatment</span></h1>
</section>

<section class="blurbs container grid grid-2 md-down-1">
  <div>
    <h3 class="t-title t-bold">Prevention</h3>
    <p class="t-lead">While ~80% of cancers are thought to be preventable, only ~5% of funding goes toward prevention.</p>
  </div>
  <div>
    <h3 class="t-title t-bold">Treatment</h3>
    <p class="t-lead">The number of cancer treatments has exploded—matching each patient with the right drug is crucial.</p>
  </div>
</section>

<section class="home-bodygrid">
  <div class="grid grid-2 md-down-1">
    <!-- LEFT: body text -->
    <div>
      <h2 class="t-title mb-4">Our mission</h2>
      <p class="t-body">We aim to deliver data-driven precision prevention and precision treatment. Our work broadly focuses on:</p>
      <ul class="dash-list">
        <li><strong>Why mutations occur:</strong> How lifestyle, microbes, the immune system, and DNA 3D structure leave their mark on the genome.</li>
        <li><strong>How this guides treatment:</strong> Using tumor mutations to predict which therapies will work best.</li>
        <li><strong>Building new tools:</strong> Developing computational and experimental approaches with clinicians and physicists.</li>
      </ul>
      <p class="t-body"><a href="{{ '/research/' | relative_url }}">Read more about our research…</a></p>
    </div>

    <!-- RIGHT: news (with a subtle divider) -->
    <aside class="news-col divider-left">
      <h2 class="t-title">Latest news</h2>
      <div class="news-scroller scroll-y">
        {% assign items = site.data.news | sort: "date" | reverse %}
        {% for n in items %}
          <article class="news-card">
            <h4 class="t-body t-bold mb-0">
              {% if n.link %}<a href="{{ n.link }}" target="_blank" rel="noopener">{{ n.headline }}</a>
              {% else %}{{ n.headline }}{% endif %}
            </h4>
            <small class="t-muted">{{ n.date | date: "%b %-d, %Y" }}</small>
            {% if n.body %}<p class="t-body mb-0">{{ n.body }}</p>{% endif %}
          </article>
        {% endfor %}
      </div>
    </aside>
  </div>
</section>
