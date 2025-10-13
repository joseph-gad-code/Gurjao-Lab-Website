---
layout: default
title: Home
---

<div class="homepage-hero-image">
  <img
    class="hero-image"
    src="{{ '/assets/images/homepage-images/homepage-hero-image.png' | relative_url }}"
    decoding="async"
    fetchpriority="high">
</div>



<div class="homepage-tagline">
  We study cancer genomes for <br>
  <span class="underlined-tagline-text">Prevention</span> and <span class="underlined-tagline-text">Treatment</span>
</div>



<section class="homepage-blurbs">
  <div class="secondary-blurb">
    <p class="main-blurb">
      While 80% of cancers are thought to be preventable, only about 5% of cancer
      funding goes toward prevention.
    </p>
    <p>
      By understanding how mutations occur, we are moving science closer to
      stopping cancer before it starts and spreads.
    </p>
  </div>
  <div class="secondary-blurb">
    <p class="main-blurb">
      The number of cancer treatments has exploded in recent years, creating a
      new challenge: ensuring each patient is matched with the right drug(s).
    </p>
    <p>
      By decoding each tumor’s genetic profile, we are informing tailored cancer
      treatments.
    </p>
  </div>
</section>



<section class="homepage-body-and-news">
  <div class="homepage-body">

    <!-- LEFT: Main body text for the homepage -->
    <div class="body-text">
      <h2>Our mission</h2>
      <p class="text-above-list">
        We aim to deliver data-driven precision prevention and precision treatment.<br>
        Our work broadly focuses on:
      </p>
      <ul>
        <li><strong>Why mutations occur:</strong> How lifestyle, microbes, the immune system, and DNA three-dimensional structure leave their mark on the genome.</li>
        <li><strong>How this knowledge guides treatment:</strong> Using tumor mutations to predict which therapies will work best.</li>
        <li><strong>Building new tools:</strong> Developing computational and experimental approaches with clinicians and physicists to push cancer research forward.</li>
      </ul>
      <p class="read-more">
        <a href="{{ '/research/' | relative_url }}">Read more about our research…</a>
      </p>
    </div>

    <!-- RIGHT: News column for the homepage -->
    <aside class="home-news" aria-label="Recent news">
      <h2>Latest news</h2>
      {% assign items = site.data.news | sort: "date" | reverse %}
      <div class="news-scroller">
        {% if items and items.size > 0 %}
          {% for n in items %}
            <article class="news-card{% if n.image %} has-media{% endif %}">
              <div class="news-content">
                <h4 class="news-headline">
                  {% if n.link %}
                    <a href="{{ n.link }}" target="_blank" rel="noopener noreferrer">{{ n.headline }}</a>
                  {% else %}
                    {{ n.headline }}
                  {% endif %}
                </h4>
                <div class="news-meta">{{ n.date | date: "%b %-d, %Y" }}</div>
                {% if n.body %}<p class="news-text">{{ n.body }}</p>{% endif %}
              </div>

              {% if n.image %}
                <a class="news-media" href="{{ n.link | default: '#' }}"
                   {% if n.link %}target="_blank" rel="noopener noreferrer"{% endif %} aria-label="Open news">
                  <img loading="lazy" src="{{ n.image | relative_url }}" alt="{{ n.headline | escape }}">
                </a>
              {% endif %}
            </article>
          {% endfor %}
        {% else %}
          <article class="news-card">
            <div class="news-content">
              <h4 class="news-headline">No news yet</h4>
              <div class="news-meta">{{ "now" | date: "%b %-d, %Y" }}</div>
              <p class="news-text">Check back soon for updates.</p>
            </div>
          </article>
        {% endif %}
      </div>
    </aside>

  </div>
</section>
