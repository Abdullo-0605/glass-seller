'use client';

import { useState, useEffect } from 'react';
import { Plus, Truck, Check, Package, Trash2 } from 'lucide-react';

interface Product {
    id: string;
    name: string;
}

interface ShipmentItem {
    id: string;
    quantity: number;
    unitCost: number;
    product: Product;
}

interface Shipment {
    id: string;
    supplier: string;
    invoiceNumber: string;
    totalCost: number;
    status: string;
    notes: string;
    createdAt: string;
    items: ShipmentItem[];
}

export default function ShipmentsPage() {
    const [shipments, setShipments] = useState<Shipment[]>([]);
    const [products, setProducts] = useState<Product[]>([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [form, setForm] = useState({
        supplier: '',
        invoiceNumber: '',
        totalCost: '',
        notes: '',
    });
    const [formItems, setFormItems] = useState<{ productId: string; quantity: string; unitCost: string }[]>([
        { productId: '', quantity: '', unitCost: '' },
    ]);

    useEffect(() => {
        loadData();
    }, []);

    async function loadData() {
        setLoading(true);
        const [shipRes, prodRes] = await Promise.all([
            fetch('/api/shipments'),
            fetch('/api/products'),
        ]);
        setShipments(await shipRes.json());
        setProducts(await prodRes.json());
        setLoading(false);
    }

    async function handleCreate(e: React.FormEvent) {
        e.preventDefault();
        const res = await fetch('/api/shipments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ...form,
                totalCost: parseFloat(form.totalCost),
                items: formItems.filter(item => item.productId).map(item => ({
                    productId: item.productId,
                    quantity: parseInt(item.quantity),
                    unitCost: parseFloat(item.unitCost),
                })),
            }),
        });
        if (res.ok) {
            setShowModal(false);
            setForm({ supplier: '', invoiceNumber: '', totalCost: '', notes: '' });
            setFormItems([{ productId: '', quantity: '', unitCost: '' }]);
            loadData();
        }
    }

    async function handleReceive(id: string) {
        await fetch(`/api/shipments/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'RECEIVED' }),
        });
        loadData();
    }

    async function handleDelete(id: string) {
        await fetch(`/api/shipments/${id}`, { method: 'DELETE' });
        loadData();
    }

    function addItem() {
        setFormItems([...formItems, { productId: '', quantity: '', unitCost: '' }]);
    }

    function updateItem(index: number, field: string, value: string) {
        const updated = [...formItems];
        updated[index] = { ...updated[index], [field]: value };
        setFormItems(updated);
    }

    function removeItem(index: number) {
        setFormItems(formItems.filter((_, i) => i !== index));
    }

    if (loading) {
        return <div className="loading"><div className="spinner" /></div>;
    }

    return (
        <div>
            <div className="admin-header">
                <h1>Wholesale Shipments</h1>
                <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                    <Plus size={16} /> New Shipment
                </button>
            </div>

            <div className="admin-card">
                <table className="admin-table">
                    <thead>
                        <tr>
                            <th>Supplier</th>
                            <th>Invoice #</th>
                            <th>Items</th>
                            <th>Total Cost</th>
                            <th>Status</th>
                            <th>Date</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {shipments.length === 0 ? (
                            <tr>
                                <td colSpan={7}>
                                    <div className="empty-state">
                                        <Truck size={40} />
                                        <h3>No shipments yet</h3>
                                        <p>Add your first wholesale shipment</p>
                                    </div>
                                </td>
                            </tr>
                        ) : (
                            shipments.map(shipment => (
                                <tr key={shipment.id}>
                                    <td><strong>{shipment.supplier}</strong></td>
                                    <td>{shipment.invoiceNumber || '—'}</td>
                                    <td>
                                        {shipment.items.map(item => (
                                            <div key={item.id} style={{ fontSize: '0.85rem', color: 'var(--gray-600)' }}>
                                                {item.product.name} × {item.quantity}
                                            </div>
                                        ))}
                                    </td>
                                    <td><strong>${shipment.totalCost.toFixed(2)}</strong></td>
                                    <td>
                                        <span className={`status-badge ${shipment.status.toLowerCase()}`}>
                                            {shipment.status}
                                        </span>
                                    </td>
                                    <td>{new Date(shipment.createdAt).toLocaleDateString()}</td>
                                    <td>
                                        <div className="btn-group">
                                            {shipment.status === 'PENDING' && (
                                                <button className="btn btn-success btn-sm" onClick={() => handleReceive(shipment.id)}>
                                                    <Check size={14} /> Receive
                                                </button>
                                            )}
                                            <button className="btn btn-danger btn-sm" onClick={() => handleDelete(shipment.id)}>
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

            {/* New Shipment Modal */}
            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>New Wholesale Shipment</h2>
                            <button className="cart-close-btn" onClick={() => setShowModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleCreate}>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label>Supplier Name *</label>
                                    <input required value={form.supplier} onChange={e => setForm({ ...form, supplier: e.target.value })} placeholder="e.g. ABC Glass Co." />
                                </div>
                                <div className="form-group">
                                    <label>Invoice Number</label>
                                    <input value={form.invoiceNumber} onChange={e => setForm({ ...form, invoiceNumber: e.target.value })} placeholder="INV-001" />
                                </div>
                                <div className="form-group">
                                    <label>Total Cost *</label>
                                    <input required type="number" step="0.01" value={form.totalCost} onChange={e => setForm({ ...form, totalCost: e.target.value })} placeholder="0.00" />
                                </div>
                                <div className="form-group">
                                    <label>Notes</label>
                                    <textarea value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} placeholder="Optional notes..." />
                                </div>

                                <h3 style={{ marginTop: 16, marginBottom: 12 }}>Shipment Items</h3>
                                {formItems.map((item, idx) => (
                                    <div key={idx} style={{ display: 'flex', gap: 8, marginBottom: 8, alignItems: 'end' }}>
                                        <div className="form-group" style={{ flex: 2 }}>
                                            {idx === 0 && <label>Product</label>}
                                            <select
                                                value={item.productId}
                                                onChange={e => updateItem(idx, 'productId', e.target.value)}
                                                style={{ padding: '10px 12px', border: '1.5px solid var(--gray-200)', borderRadius: 'var(--radius-sm)', fontSize: '0.9rem', fontFamily: 'Inter', width: '100%' }}
                                            >
                                                <option value="">Select product</option>
                                                {products.map(p => (
                                                    <option key={p.id} value={p.id}>{p.name}</option>
                                                ))}
                                            </select>
                                        </div>
                                        <div className="form-group" style={{ flex: 1 }}>
                                            {idx === 0 && <label>Qty</label>}
                                            <input type="number" value={item.quantity} onChange={e => updateItem(idx, 'quantity', e.target.value)} placeholder="0" />
                                        </div>
                                        <div className="form-group" style={{ flex: 1 }}>
                                            {idx === 0 && <label>Unit Cost</label>}
                                            <input type="number" step="0.01" value={item.unitCost} onChange={e => updateItem(idx, 'unitCost', e.target.value)} placeholder="0.00" />
                                        </div>
                                        {formItems.length > 1 && (
                                            <button type="button" className="btn btn-outline btn-sm" onClick={() => removeItem(idx)} style={{ marginBottom: 6 }}>
                                                <Trash2 size={14} />
                                            </button>
                                        )}
                                    </div>
                                ))}
                                <button type="button" className="btn btn-outline btn-sm" onClick={addItem}>
                                    <Plus size={14} /> Add Item
                                </button>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-outline" onClick={() => setShowModal(false)}>Cancel</button>
                                <button type="submit" className="btn btn-primary">Create Shipment</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
