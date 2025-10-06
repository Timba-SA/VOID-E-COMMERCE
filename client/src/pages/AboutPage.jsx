// En client/src/pages/AboutPage.jsx
import React from 'react';
import heroImage from '/img/PortadaDerecha.jpg'; // 1. Importamos la imagen

const AboutPage = () => {

  // 2. Función para hacer el scroll suave
  const handleScrollDown = () => {
    const section = document.getElementById('our-philosophy');
    if (section) {
      section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <main className="about-page">
      <section className="about-hero">
        <div className="about-hero-background">
          {/* 3. Usamos la imagen importada y le ponemos la clase de animación */}
          <img 
            src={heroImage} 
            alt="Concepto de VOID" 
            className="hero-image-entry"
          />
        </div>
        <div className="about-hero-title">
          <h1>THE CONCEPT BEHIND THE VOID</h1>
          {/* 4. Agregamos el botón fachero */}
          <button onClick={handleScrollDown} className="read-more-btn">
            READ MORE
          </button>
        </div>
      </section>

      <div className="about-content">
        {/* 5. Le ponemos un 'id' a la sección para que el botón sepa a dónde ir */}
        <section id="our-philosophy" className="about-content-section philosophy">
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