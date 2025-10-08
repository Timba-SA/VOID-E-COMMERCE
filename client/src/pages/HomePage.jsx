// client/src/pages/HomePage.jsx

import React, { useState, useEffect, useRef } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { getProducts } from '../api/productsApi';
import ProductCard from '../components/products/ProductCard';

import portadaIzquierda from '/img/PortadaIzquierda.jpg';
import portadaDerecha from '/img/PortadaDerecha.jpg';

gsap.registerPlugin(ScrollTrigger);

const HomePage = () => {
  const [products, setProducts] = useState([]);
  const titleRef = useRef(null); // Referencia para el título

  useEffect(() => {
    const fetchAndAnimateProducts = async () => {
      try {
        const fetchedProducts = await getProducts({ limit: 6 });
        setProducts(fetchedProducts);
      } catch (error) {
        console.error("Error al cargar los productos:", error);
      }
    };

    fetchAndAnimateProducts();

    // ¡LA NUEVA ANIMACIÓN DEL TÍTULO!
    if (titleRef.current) {
        const el = titleRef.current;
        const chars = el.innerText.split('');
        el.innerHTML = chars.map(char => `<span>${char === ' ' ? '&nbsp;' : char}</span>`).join('');

        gsap.fromTo(el.children,
            { y: 50, opacity: 0 },
            {
                y: 0,
                opacity: 1,
                duration: 1.2,
                stagger: 0.08,
                ease: 'power4.out',
                scrollTrigger: {
                    trigger: el,
                    start: 'top 85%',
                }
            }
        );
    }

    gsap.to(".new-arrivals", {
      opacity: 1,
      y: 0,
      duration: 1.5,
      delay: 0.5
    });

  }, []); // El array vacío asegura que la animación del título se configure una sola vez

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
          <img
            src={portadaIzquierda}
            alt="Modelo con prenda vanguardista"
            className="hero-image-entry" 
          />
        </div>
        <div className="hero-image-right">
          <img
            src={portadaDerecha}
            alt="Modelo con traje sastre oscuro"
            className="hero-image-entry"
          />
        </div>
      </section>

      <section className="new-arrivals">
        <div className="title-the-new-container">
            <h2 className="title-the-new-text" ref={titleRef}>THE NEW</h2>
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