import React, { useState, useEffect } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { getProducts } from '../api/productsApi';
import ProductCard from '../components/products/ProductCard';

gsap.registerPlugin(ScrollTrigger);

const HomePage = () => {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    const fetchAndAnimate = async () => {
      try {
        const fetchedProducts = await getProducts({ limit: 6 }); 
        setProducts(fetchedProducts);
      } catch (error) {
        console.error("Error al cargar los productos:", error);
      }
    };

    fetchAndAnimate();

    gsap.to(".new-arrivals", {
      opacity: 1,
      y: 0,
      duration: 1.5,
      delay: 0.5
    });
  }, []);

  useEffect(() => {
    if (products.length > 0) {
      gsap.fromTo(".product-card",
        { opacity: 0, y: 50 },
        {
          opacity: 1,
          y: 0,
          duration: 0.8,
          stagger: 0.2,
          ease: "power3.out",
          scrollTrigger: {
            trigger: ".product-grid",
            start: "top 80%",
          }
        }
      );
    }
  }, [products]);

  return (
    <main>
      <section className="hero-section">
        <div className="hero-image-left">
          <img src="/img/PortadaIzquierda.jpg" alt="Modelo con prenda vanguardista" />
        </div>
        <div className="hero-image-right">
          <img src="/img/PortadaDerecha.jpg" alt="Modelo con traje sastre oscuro" />
        </div>
      </section>

      <section className="new-arrivals">
        {/* --- ¡ACÁ ESTÁ EL CAMBIO, CAMPEÓN! --- */}
        <div className="title-the-new-container">
            <h2 className="title-the-new-text">THE NEW</h2>
            <div className="title-the-new-line"></div>
        </div>
        {/* --- FIN DEL CAMBIO --- */}

        <div className="product-grid">
          {products.map(product => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      </section>
    </main>
  );
};

export default HomePage;