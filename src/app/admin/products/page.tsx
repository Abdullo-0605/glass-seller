'use client';

import { useState, useEffect } from 'react';
import { Plus, Pencil, Trash2, Package } from 'lucide-react';

interface Product {
    id: string;
    name: string;
    description: string;
    category: string;
    price: number;
    stockQuantity: number;
    imageUrl: string;
}

export default function ProductsPage() {
    const [products, setProducts] = useState<Product[]>([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editingProduct, setEditingProduct] = useState<Product | null>(null);
    const [form, setForm] = useState({
        name: '',
        description: '',
        category: 'Windshield',
        price: '',
        stockQuantity: '',
        imageUrl: '',
    });

    const categories = ['Windshield', 'Tempered Glass', 'Mirror', 'Window', 'Custom', 'Accessories'];

    useEffect(() => {
        loadProducts();
    }, []);

    async function loadProducts() {
        setLoading(true);
        const res = await fetch('/api/products');
        setProducts(await res.json());
        setLoading(false);
    }

    function openEdit(product: Product) {
        setEditingProduct(product);
        setForm({
            name: product.name,
            description: product.description,
            category: product.category,
            price: String(product.price),
            stockQuantity: String(product.stockQuantity),
            imageUrl: product.imageUrl,
        });
        setShowModal(true);
    }

    function openCreate() {
        setEditingProduct(null);
        setForm({ name: '', description: '', category: 'Windshield', price: '', stockQuantity: '', imageUrl: '' });
        setShowModal(true);
    }

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        const url = editingProduct ? `/api/products/${editingProduct.id}` : '/api/products';
        const method = editingProduct ? 'PUT' : 'POST';
        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(form),
        });
        if (res.ok) {
            setShowModal(false);
            loadProducts();
        }
    }

    async function handleDelete(id: string) {
        if (!confirm('Are you sure you want to delete this product?')) return;
        await fetch(`/api/products/${id}`, { method: 'DELETE' });
        loadProducts();
    }

    if (loading) {
        return <div className="loading"><div className="spinner" /></div>;
    }

    return (
        <div>
            <div className="admin-header">
                <h1>Products</h1>
                <button className="btn btn-primary" onClick={openCreate}>
                    <Plus size={16} /> Add Product
                </button>
            </div>

            <div className="admin-card">
                <table className="admin-table">
                    <thead>
                        <tr>
                            <th>Product</th>
                            <th>Category</th>
                            <th>Price</th>
                            <th>Stock</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {products.length === 0 ? (
                            <tr>
                                <td colSpan={5}>
                                    <div className="empty-state">
                                        <Package size={40} />
                                        <h3>No products yet</h3>
                                        <p>Add your first product to get started</p>
                                    </div>
                                </td>
                            </tr>
                        ) : (
                            products.map(product => (
                                <tr key={product.id}>
                                    <td>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                            <div style={{
                                                width: 40, height: 40, borderRadius: 'var(--radius-sm)',
                                                background: 'var(--primary-50)', display: 'flex',
                                                alignItems: 'center', justifyContent: 'center',
                                                color: 'var(--primary-300)', overflow: 'hidden', flexShrink: 0
                                            }}>
                                                {product.imageUrl ? (
                                                    <img src={product.imageUrl} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                                                ) : (
                                                    <Package size={18} />
                                                )}
                                            </div>
                                            <div>
                                                <strong>{product.name}</strong>
                                                <div style={{ fontSize: '0.8rem', color: 'var(--gray-500)' }}>{product.description?.slice(0, 50)}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td><span className="product-card-category">{product.category}</span></td>
                                    <td><strong>${product.price.toFixed(2)}</strong></td>
                                    <td>
                                        <span className={`product-card-stock ${product.stockQuantity <= 0 ? 'out' : product.stockQuantity <= 5 ? 'low' : ''}`}>
                                            {product.stockQuantity}
                                        </span>
                                    </td>
                                    <td>
                                        <div className="btn-group">
                                            <button className="btn btn-outline btn-sm" onClick={() => openEdit(product)}>
                                                <Pencil size={14} /> Edit
                                            </button>
                                            <button className="btn btn-danger btn-sm" onClick={() => handleDelete(product.id)}>
                                                <Trash2 size={14} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>{editingProduct ? 'Edit Product' : 'Add Product'}</h2>
                            <button className="cart-close-btn" onClick={() => setShowModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleSubmit}>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label>Product Name *</label>
                                    <input required value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="e.g. Front Windshield - Toyota Camry 2020" />
                                </div>
                                <div className="form-group">
                                    <label>Description</label>
                                    <textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="Product description..." />
                                </div>
                                <div className="form-group">
                                    <label>Category</label>
                                    <select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} style={{ padding: '10px 12px', border: '1.5px solid var(--gray-200)', borderRadius: 'var(--radius-sm)', fontSize: '0.9rem', fontFamily: 'Inter' }}>
                                        {categories.map(cat => (
                                            <option key={cat} value={cat}>{cat}</option>
                                        ))}
                                    </select>
                                </div>
                                <div style={{ display: 'flex', gap: 12 }}>
                                    <div className="form-group" style={{ flex: 1 }}>
                                        <label>Price ($) *</label>
                                        <input required type="number" step="0.01" value={form.price} onChange={e => setForm({ ...form, price: e.target.value })} placeholder="0.00" />
                                    </div>
                                    <div className="form-group" style={{ flex: 1 }}>
                                        <label>Initial Stock</label>
                                        <input type="number" value={form.stockQuantity} onChange={e => setForm({ ...form, stockQuantity: e.target.value })} placeholder="0" />
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label>Image URL</label>
                                    <input type="url" value={form.imageUrl} onChange={e => setForm({ ...form, imageUrl: e.target.value })} placeholder="https://..." />
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-outline" onClick={() => setShowModal(false)}>Cancel</button>
                                <button type="submit" className="btn btn-primary">{editingProduct ? 'Save Changes' : 'Add Product'}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
