import React, { useState, useEffect } from 'react';
import Slider from 'rc-slider';
import 'rc-slider/assets/index.css';

const FilterPanel = ({ isOpen, onClose, onFilterChange, initialFilters, categories = [] }) => {
  const [priceRange, setPriceRange] = useState([initialFilters.precio_min, initialFilters.precio_max]);
  const [selectedSizes, setSelectedSizes] = useState(initialFilters.talle || []);
  const [selectedColors, setSelectedColors] = useState(initialFilters.color || []);
  const [selectedCategory, setSelectedCategory] = useState(initialFilters.categoria_id || '');
  
  const availableColors = ['Black', 'White', 'Grey', 'Brown', 'Beige', 'Blue'];
  const minPrice = 0;
  const maxPrice = 200000;

  useEffect(() => {
    setPriceRange([initialFilters.precio_min, initialFilters.precio_max]);
    setSelectedSizes(initialFilters.talle || []);
    setSelectedColors(initialFilters.color || []);
    setSelectedCategory(initialFilters.categoria_id || '');
  }, [initialFilters]);

  const handlePriceChange = (newRange) => {
    setPriceRange(newRange);
  };

  const handleApplyPriceFilter = (newRange) => {
    onFilterChange({ precio_min: newRange[0], precio_max: newRange[1] });
  };

  const handleSizeChange = (e) => {
    const { value, checked } = e.target;
    const newSizes = checked 
      ? [...selectedSizes, value] 
      : selectedSizes.filter(size => size !== value);
    
    setSelectedSizes(newSizes);
    onFilterChange({ talle: newSizes });
  };
  
  const handleColorChange = (e) => {
    const { value, checked } = e.target;
    const newColors = checked
      ? [...selectedColors, value]
      : selectedColors.filter(color => color !== value);

    setSelectedColors(newColors);
    onFilterChange({ color: newColors });
  };

  const handleSortChange = (e) => {
    onFilterChange({ sort_by: e.target.value });
  };

  const handleCategoryChange = (e) => {
    const newCategoryId = e.target.value;
    setSelectedCategory(newCategoryId);
    onFilterChange({ categoria_id: newCategoryId });
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency', currency: 'ARS',
      minimumFractionDigits: 0, maximumFractionDigits: 0,
    }).format(price).replace("ARS", "").trim();
  };

  return (
    <div className={`filter-panel ${isOpen ? 'open' : ''}`}>
      <div className="filter-panel-header">
        <h2 className="filter-panel-title">FILTERS</h2>
        <button className="filter-panel-close-btn" onClick={onClose}>
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M1 1L17 17M17 1L1 17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        </button>
      </div>

      <div className="filter-panel-content">
        <div className="filter-section active">
          <div className="filter-section-header">
            <span className="filter-section-title">SORT BY</span>
          </div>
          <div className="filter-section-body">
            <select 
              className="sort-dropdown-panel" 
              value={initialFilters.sort_by} 
              onChange={handleSortChange}
            >
              <option value="nombre_asc">Name (A-Z)</option>
              <option value="nombre_desc">Name (Z-A)</option>
              <option value="precio_asc">Price (Low to High)</option>
              <option value="precio_desc">Price (High to Low)</option>
            </select>
          </div>
        </div>

        <div className="filter-section active">
            <div className="filter-section-header">
                <span className="filter-section-title">CATEGORY</span>
            </div>
            <div className="filter-section-body">
                <label className="radio-container">
                    <input 
                        type="radio" 
                        name="category" 
                        value="" 
                        checked={!selectedCategory} 
                        onChange={handleCategoryChange} 
                    /> All
                    <span className="radiomark"></span>
                </label>
                {categories.map(category => (
                    <label className="radio-container" key={category.id}>
                        <input 
                            type="radio" 
                            name="category" 
                            value={category.id} 
                            checked={selectedCategory === category.id.toString()} 
                            onChange={handleCategoryChange} 
                        /> {category.nombre}
                        <span className="radiomark"></span>
                    </label>
                ))}
            </div>
        </div>

        <div className="filter-section active">
          <div className="filter-section-header">
            <span className="filter-section-title">SIZE</span>
          </div>
          <div className="filter-section-body">
            {['XS', 'S', 'M', 'L', 'XL', 'XXL'].map(size => (
              <label className="checkbox-container" key={size}>
                <input 
                  type="checkbox" 
                  name="size" 
                  value={size} 
                  checked={selectedSizes.includes(size)}
                  onChange={handleSizeChange}
                /> {size}
                <span className="checkmark"></span>
              </label>
            ))}
          </div>
        </div>

        <div className="filter-section active">
          <div className="filter-section-header">
            <span className="filter-section-title">PRICE</span>
          </div>
          <div className="filter-section-body price-filter-body">
            <div className="price-display">
              <span className="price-value">{formatPrice(priceRange[0])} ARS</span>
              <span className="price-separator">-</span>
              <span className="price-value">{formatPrice(priceRange[1])} ARS</span>
            </div>
            <Slider
              range
              min={minPrice}
              max={maxPrice}
              step={1000}
              value={priceRange}
              onChange={handlePriceChange}
              onChangeComplete={handleApplyPriceFilter}
              trackStyle={[{ backgroundColor: 'black', height: 2 }]}
              handleStyle={[{ backgroundColor: 'black', borderColor: 'black', height: 10, width: 10, marginTop: -4, boxShadow: 'none' }, { backgroundColor: 'black', borderColor: 'black', height: 10, width: 10, marginTop: -4, boxShadow: 'none'}]}
              railStyle={{ backgroundColor: '#ccc', height: 2 }}
            />
          </div>
        </div>
        
        <div className="filter-section active">
          <div className="filter-section-header">
            <span className="filter-section-title">COLOR</span>
          </div>
          <div className="filter-section-body">
            {availableColors.map(color => (
              <label className="checkbox-container" key={color}>
                <input 
                  type="checkbox" 
                  name="color" 
                  value={color}
                  checked={selectedColors.includes(color)}
                  onChange={handleColorChange}
                /> {color}
                <span className="checkmark"></span>
              </label>
            ))}
          </div>
        </div>
        
      </div>
    </div>
  );
};

export default FilterPanel;