'use client';

import { useState, useEffect } from 'react';
import { Check, X, ShoppingBag, Mail, Phone, MapPin } from 'lucide-react';

interface OrderItem {
    id: string;
    quantity: number;
    price: number;
    product: { id: string; name: string };
}

interface Order {
    id: string;
    customerName: string;
    customerEmail: string;
    customerPhone: string;
    customerAddress: string;
    status: string;
    totalAmount: number;
    notes: string;
    createdAt: string;
    items: OrderItem[];
}

export default function OrdersPage() {
    const [orders, setOrders] = useState<Order[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('ALL');
    const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);

    useEffect(() => {
        loadOrders();
    }, []);

    async function loadOrders() {
        setLoading(true);
        const res = await fetch('/api/orders');
        setOrders(await res.json());
        setLoading(false);
    }

    async function updateStatus(id: string, status: string) {
        await fetch(`/api/orders/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status }),
        });
        setSelectedOrder(null);
        loadOrders();
    }

    const filteredOrders = filter === 'ALL'
        ? orders
        : orders.filter(o => o.status === filter);

    if (loading) {
        return <div className="loading"><div className="spinner" /></div>;
    }

    return (
        <div>
            <div className="admin-header">
                <h1>Customer Orders</h1>
                <div className="btn-group">
                    {['ALL', 'PENDING', 'APPROVED', 'REJECTED'].map(f => (
                        <button
                            key={f}
                            className={`btn btn-sm ${filter === f ? 'btn-primary' : 'btn-outline'}`}
                            onClick={() => setFilter(f)}
                        >
                            {f === 'ALL' ? 'All' : f.charAt(0) + f.slice(1).toLowerCase()}
                            {f !== 'ALL' && (
                                <span style={{ marginLeft: 4, opacity: 0.7 }}>
                                    ({orders.filter(o => f === 'ALL' || o.status === f).length})
                                </span>
                            )}
                        </button>
                    ))}
                </div>
            </div>

            <div className="admin-card">
                <table className="admin-table">
                    <thead>
                        <tr>
                            <th>Customer</th>
                            <th>Items</th>
                            <th>Total</th>
                            <th>Status</th>
                            <th>Date</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredOrders.length === 0 ? (
                            <tr>
                                <td colSpan={6}>
                                    <div className="empty-state">
                                        <ShoppingBag size={40} />
                                        <h3>No orders found</h3>
                                        <p>{filter !== 'ALL' ? `No ${filter.toLowerCase()} orders` : 'Orders will appear here when customers check out'}</p>
                                    </div>
                                </td>
                            </tr>
                        ) : (
                            filteredOrders.map(order => (
                                <tr key={order.id}>
                                    <td>
                                        <div>
                                            <strong>{order.customerName}</strong>
                                            <div style={{ fontSize: '0.8rem', color: 'var(--gray-500)' }}>
                                                {order.customerEmail}
                                            </div>
                                        </div>
                                    </td>
                                    <td>
                                        {order.items.map(item => (
                                            <div key={item.id} style={{ fontSize: '0.85rem', color: 'var(--gray-600)' }}>
                                                {item.product.name} × {item.quantity}
                                            </div>
                                        ))}
                                    </td>
                                    <td><strong>${order.totalAmount.toFixed(2)}</strong></td>
                                    <td>
                                        <span className={`status-badge ${order.status.toLowerCase()}`}>
                                            {order.status}
                                        </span>
                                    </td>
                                    <td>{new Date(order.createdAt).toLocaleDateString()}</td>
                                    <td>
                                        <div className="btn-group">
                                            <button className="btn btn-outline btn-sm" onClick={() => setSelectedOrder(order)}>
                                                View
                                            </button>
                                            {order.status === 'PENDING' && (
                                                <>
                                                    <button className="btn btn-success btn-sm" onClick={() => updateStatus(order.id, 'APPROVED')}>
                                                        <Check size={14} /> Approve
                                                    </button>
                                                    <button className="btn btn-danger btn-sm" onClick={() => updateStatus(order.id, 'REJECTED')}>
                                                        <X size={14} /> Reject
                                                    </button>
                                                </>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Order Detail Modal */}
            {selectedOrder && (
                <div className="modal-overlay" onClick={() => setSelectedOrder(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>Order Details</h2>
                            <button className="cart-close-btn" onClick={() => setSelectedOrder(null)}>×</button>
                        </div>
                        <div className="modal-body">
                            <div style={{ marginBottom: 16 }}>
                                <span className={`status-badge ${selectedOrder.status.toLowerCase()}`}>
                                    {selectedOrder.status}
                                </span>
                                <span style={{ marginLeft: 8, fontSize: '0.85rem', color: 'var(--gray-500)' }}>
                                    {new Date(selectedOrder.createdAt).toLocaleString()}
                                </span>
                            </div>

                            <h3 style={{ fontSize: '1rem', marginBottom: 12 }}>Customer Info</h3>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 20 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.9rem' }}>
                                    <strong>{selectedOrder.customerName}</strong>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem', color: 'var(--gray-600)' }}>
                                    <Mail size={14} /> {selectedOrder.customerEmail}
                                </div>
                                {selectedOrder.customerPhone && (
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem', color: 'var(--gray-600)' }}>
                                        <Phone size={14} /> {selectedOrder.customerPhone}
                                    </div>
                                )}
                                {selectedOrder.customerAddress && (
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem', color: 'var(--gray-600)' }}>
                                        <MapPin size={14} /> {selectedOrder.customerAddress}
                                    </div>
                                )}
                            </div>

                            <h3 style={{ fontSize: '1rem', marginBottom: 12 }}>Order Items</h3>
                            {selectedOrder.items.map(item => (
                                <div key={item.id} className="checkout-item">
                                    <span>{item.product.name} × {item.quantity}</span>
                                    <strong>${(item.price * item.quantity).toFixed(2)}</strong>
                                </div>
                            ))}
                            <hr className="checkout-divider" />
                            <div className="checkout-grand-total">
                                <span>Total</span>
                                <span>${selectedOrder.totalAmount.toFixed(2)}</span>
                            </div>

                            {selectedOrder.notes && (
                                <div style={{ marginTop: 16, padding: 12, background: 'var(--gray-50)', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem', color: 'var(--gray-600)' }}>
                                    <strong>Notes:</strong> {selectedOrder.notes}
                                </div>
                            )}
                        </div>
                        {selectedOrder.status === 'PENDING' && (
                            <div className="modal-footer">
                                <button className="btn btn-danger" onClick={() => updateStatus(selectedOrder.id, 'REJECTED')}>
                                    <X size={16} /> Reject
                                </button>
                                <button className="btn btn-success" onClick={() => updateStatus(selectedOrder.id, 'APPROVED')}>
                                    <Check size={16} /> Approve
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
