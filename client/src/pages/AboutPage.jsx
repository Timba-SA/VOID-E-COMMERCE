// En client/src/pages/AboutPage.jsx

import React from 'react';

const AboutPage = () => {
  return (
    <main className="about-page">
      <section className="about-hero">
        <div className="about-hero-background">
          <img src="/img/PortadaDerecha.jpg" alt="Concepto de VOID" />
        </div>
        <div className="about-hero-title">
          <h1>THE CONCEPT BEHIND THE VOID</h1>
        </div>
      </section>

      <div className="about-content">
        <section className="about-content-section philosophy">
          <div className="section-title-wrapper">
            <h2 className="section-title">OUR PHILOSOPHY</h2>
            <div className="section-line"></div>
          </div>
          <div className="section-text">
            <p>
              VOID is not just an apparel brand; <strong>it's a statement</strong>. We were born from the idea that ultimate sophistication lies in simplicity. We believe in the power of pure silhouettes, high-quality materials, and a color palette that transcends seasons.
            </p>
            <p>
              Each piece is meticulously designed in our atelier, with timelessness and versatility in mind. We create clothes for individuals who don't follow trends but define their own style. The void is not absence; it is a canvas of infinite possibilities.
            </p>
          </div>
        </section>

        <section className="about-content-section commitment">
          <div className="section-title-wrapper">
            <h2 className="section-title">OUR COMMITMENT</h2>
            <div className="section-line"></div>
          </div>
          <div className="section-text">
            <p>
              We are committed to craftsmanship and sustainability. We collaborate with small workshops and carefully select each textile, ensuring not only an impeccable aesthetic but also ethical and responsible production.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
};

export default AboutPage;