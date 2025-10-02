// client/src/pages/HomePage.jsx

import React, { useState, useEffect } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { getProducts } from '../api/productsApi';
import ProductCard from '../components/products/ProductCard';

import portadaIzquierda from '/img/PortadaIzquierda.jpg';
import portadaDerecha from '/img/PortadaDerecha.jpg';

gsap.registerPlugin(ScrollTrigger);

const HomePage = () => {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    // SACAMOS LA ANIMACIÓN GSAP DE LAS IMÁGENES DE ACÁ PARA QUE NO JODA
    
    const fetchAndAnimateProducts = async () => {
      try {
        const fetchedProducts = await getProducts({ limit: 6 });
        setProducts(fetchedProducts);
      } catch (error) {
        console.error("Error al cargar los productos:", error);
      }
    };

    fetchAndAnimateProducts();

    gsap.to(".new-arrivals", {
      opacity: 1,
      y: 0,
      duration: 1.5,
      delay: 0.5
    });
  }, []);

  useEffect(() => {
    if (products.length > 0) {
      gsap.fromTo(".product-card-home",
        { opacity: 0, y: 50 },
        {
          opacity: 1,
          y: 0,
          duration: 0.8,
          stagger: 0.2,
          ease: "power3.out",
          scrollTrigger: {
            trigger: ".product-grid-home",
            start: "top 80%",
          }
        }
      );
    }
  }, [products]);

  return (
    <main className="home-page">
      <section className="hero-section">
        <div className="hero-image-left">
          {/* USAMOS LA NUEVA CLASE DE CSS */}
          <img
            src={portadaIzquierda}
            alt="Modelo con prenda vanguardista"
            className="hero-image-entry" 
          />
        </div>
        <div className="hero-image-right">
          {/* Y ACÁ TAMBIÉN */}
          <img
            src={portadaDerecha}
            alt="Modelo con traje sastre oscuro"
            className="hero-image-entry"
          />
        </div>
      </section>

      <section className="new-arrivals">
        <div className="title-the-new-container">
            <h2 className="title-the-new-text">THE NEW</h2>
            <div className="title-the-new-line"></div>
        </div>

        <div className="product-grid product-grid-home">
          {products.map(product => (
            <ProductCard
              key={product.id}
              product={product}
              displayMode="imageOnly"
            />
          ))}
        </div>
      </section>
    </main>
  );
};

export default HomePage;