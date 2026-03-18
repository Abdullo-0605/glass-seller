'use client';

import { useState, useEffect } from 'react';
import { Search } from 'lucide-react';
import ProductCard from '@/components/ProductCard';

interface Product {
  id: string;
  name: string;
  description: string;
  category: string;
  price: number;
  stockQuantity: number;
  imageUrl: string;
}

export default function HomePage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('All');
  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState<string[]>(['All']);

  useEffect(() => {
    fetchProducts();
  }, [search, category]);

  async function fetchProducts() {
    setLoading(true);
    const params = new URLSearchParams();
    if (search) params.set('search', search);
    if (category && category !== 'All') params.set('category', category);
    const res = await fetch(`/api/products?${params.toString()}`);
    const data = await res.json();
    setProducts(data);

    // Extract categories from all products for the filter
    if (category === 'All' && !search) {
      const cats = [...new Set(data.map((p: Product) => p.category))] as string[];
      setCategories(['All', ...cats]);
    }
    setLoading(false);
  }

  return (
    <main>
      <section className="hero">
        <h1>Premium Glass Parts</h1>
        <p>
          Browse our extensive catalog of glass parts and supplies. Search, add to cart, and submit
          your order — our team will review and approve it promptly.
        </p>
      </section>

      <section className="search-section">
        <div className="search-bar-wrapper">
          <div className="search-bar">
            <Search size={20} />
            <input
              type="text"
              placeholder="Search glass parts..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select
            className="filter-select"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>
      </section>

      <section className="products-section">
        {loading ? (
          <div className="loading">
            <div className="spinner" />
          </div>
        ) : products.length === 0 ? (
          <div className="empty-state">
            <Search size={48} />
            <h3>No products found</h3>
            <p>Try adjusting your search or filter criteria</p>
          </div>
        ) : (
          <div className="products-grid">
            {products.map(product => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
