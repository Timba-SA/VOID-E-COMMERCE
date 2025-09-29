// En FRONTEND/src/pages/AboutPage.jsx
import React from 'react';

const AboutPage = () => {
  return (
    <div className="about-page-container">
      <div className="about-hero">
        {/* Usamos la imagen que pediste como fondo */}
        <img src="/img/PortadaIzquierda.jpg" alt="Concepto de VOID" />
        <div className="about-hero-overlay">
          <h1>THE CONCEPT BEHIND THE VOID</h1>
        </div>
      </div>
      <div className="about-content">
        <h2>OUR PHILOSOPHY</h2>
        <p>
          VOID is not just an apparel brand; it's a statement. We were born from the idea that ultimate sophistication lies in simplicity. We believe in the power of pure silhouettes, high-quality materials, and a color palette that transcends seasons.
        </p>
        <p>
          Each piece is meticulously designed in our atelier, with timelessness and versatility in mind. We create clothes for individuals who don't follow trends but define their own style. The void is not absence; it is a canvas of infinite possibilities.
        </p>
        <div className="about-separator"></div>
        <h2>OUR COMMITMENT</h2>
        <p>
          We are committed to craftsmanship and sustainability. We collaborate with small workshops and carefully select each textile, ensuring not only an impeccable aesthetic but also ethical and responsible production.
        </p>
      </div>
    </div>
  );
};

export default AboutPage;