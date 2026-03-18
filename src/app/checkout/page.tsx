'use client';

import { useState } from 'react';
import { useCart } from '@/context/CartContext';
import { CheckCircle, ArrowLeft, Package } from 'lucide-react';
import Link from 'next/link';

export default function CheckoutPage() {
    const { items, totalAmount, clearCart } = useCart();
    const [submitted, setSubmitted] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState('');
    const [form, setForm] = useState({
        customerName: '',
        customerEmail: '',
        customerPhone: '',
        customerAddress: '',
        notes: '',
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        setForm({ ...form, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (items.length === 0) return;
        setSubmitting(true);
        setError('');

        try {
            const res = await fetch('/api/orders', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...form,
                    totalAmount,
                    items: items.map(item => ({
                        productId: item.id,
                        quantity: item.quantity,
                        price: item.price,
                    })),
                }),
            });

            if (!res.ok) {
                const data = await res.json();
                setError(data.error || 'Failed to submit order');
                setSubmitting(false);
                return;
            }

            clearCart();
            setSubmitted(true);
        } catch {
            setError('Network error. Please try again.');
        }
        setSubmitting(false);
    };

    if (submitted) {
        return (
            <div className="success-page">
                <div className="success-icon">
                    <CheckCircle size={40} />
                </div>
                <h1>Order Submitted!</h1>
                <p>
                    Your order has been sent to our team for review. We&apos;ll get back to you shortly once
                    it&apos;s approved.
                </p>
                <Link href="/" className="back-home-btn">
                    <ArrowLeft size={18} />
                    Back to Catalog
                </Link>
            </div>
        );
    }

    if (items.length === 0) {
        return (
            <div className="success-page">
                <div className="empty-state">
                    <Package size={48} />
                    <h3>Your cart is empty</h3>
                    <p>Add some products before checking out</p>
                </div>
                <Link href="/" className="back-home-btn" style={{ marginTop: 24 }}>
                    <ArrowLeft size={18} />
                    Browse Products
                </Link>
            </div>
        );
    }

    return (
        <div className="checkout-page">
            <h1>Checkout</h1>
            <p className="checkout-subtitle">Fill in your details and we&apos;ll review your order</p>

            {error && (
                <div className="toast error" style={{ marginBottom: 20 }}>
                    {error}
                </div>
            )}

            <div className="checkout-grid">
                <form className="checkout-form" onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="customerName">Full Name *</label>
                        <input
                            id="customerName"
                            name="customerName"
                            type="text"
                            required
                            value={form.customerName}
                            onChange={handleChange}
                            placeholder="John Doe"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="customerEmail">Email Address *</label>
                        <input
                            id="customerEmail"
                            name="customerEmail"
                            type="email"
                            required
                            value={form.customerEmail}
                            onChange={handleChange}
                            placeholder="john@example.com"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="customerPhone">Phone Number</label>
                        <input
                            id="customerPhone"
                            name="customerPhone"
                            type="tel"
                            value={form.customerPhone}
                            onChange={handleChange}
                            placeholder="(555) 123-4567"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="customerAddress">Shipping Address</label>
                        <textarea
                            id="customerAddress"
                            name="customerAddress"
                            value={form.customerAddress}
                            onChange={handleChange}
                            placeholder="123 Main St, Apt 4, City, State, ZIP"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="notes">Additional Notes</label>
                        <textarea
                            id="notes"
                            name="notes"
                            value={form.notes}
                            onChange={handleChange}
                            placeholder="Any special requests or details..."
                        />
                    </div>

                    <button
                        type="submit"
                        className="submit-order-btn"
                        disabled={submitting}
                    >
                        {submitting ? 'Submitting...' : 'Submit Order for Review'}
                    </button>
                </form>

                <div className="checkout-summary-card">
                    <h3>Order Summary</h3>
                    {items.map(item => (
                        <div key={item.id} className="checkout-item">
                            <span className="checkout-item-name">
                                {item.name} × {item.quantity}
                            </span>
                            <span className="checkout-item-total">
                                ${(item.price * item.quantity).toFixed(2)}
                            </span>
                        </div>
                    ))}
                    <hr className="checkout-divider" />
                    <div className="checkout-grand-total">
                        <span>Total</span>
                        <span>${totalAmount.toFixed(2)}</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
