'use client';

import { useCart } from '@/context/CartContext';
import { ShoppingCart, X, Minus, Plus, Trash2, Package } from 'lucide-react';
import Link from 'next/link';

export default function CartDrawer() {
    const { items, isCartOpen, setIsCartOpen, updateQuantity, removeItem, totalAmount, totalItems } = useCart();

    return (
        <>
            <div className={`cart-overlay ${isCartOpen ? 'open' : ''}`} onClick={() => setIsCartOpen(false)} />
            <div className={`cart-drawer ${isCartOpen ? 'open' : ''}`}>
                <div className="cart-drawer-header">
                    <h2>Your Cart ({totalItems})</h2>
                    <button className="cart-close-btn" onClick={() => setIsCartOpen(false)}>
                        <X size={18} />
                    </button>
                </div>

                <div className="cart-items">
                    {items.length === 0 ? (
                        <div className="cart-empty">
                            <Package size={48} />
                            <p>Your cart is empty</p>
                        </div>
                    ) : (
                        items.map(item => (
                            <div key={item.id} className="cart-item">
                                <div className="cart-item-image">
                                    {item.imageUrl ? (
                                        <img src={item.imageUrl} alt={item.name} />
                                    ) : (
                                        <Package size={24} />
                                    )}
                                </div>
                                <div className="cart-item-info">
                                    <div className="cart-item-name">{item.name}</div>
                                    <div className="cart-item-price">${item.price.toFixed(2)}</div>
                                    <div className="cart-item-controls">
                                        <button className="qty-btn" onClick={() => updateQuantity(item.id, item.quantity - 1)}>
                                            <Minus size={14} />
                                        </button>
                                        <span className="cart-item-qty">{item.quantity}</span>
                                        <button className="qty-btn" onClick={() => updateQuantity(item.id, item.quantity + 1)}>
                                            <Plus size={14} />
                                        </button>
                                        <button className="cart-item-remove" onClick={() => removeItem(item.id)}>
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {items.length > 0 && (
                    <div className="cart-drawer-footer">
                        <div className="cart-total">
                            <span className="cart-total-label">Total</span>
                            <span className="cart-total-value">${totalAmount.toFixed(2)}</span>
                        </div>
                        <Link href="/checkout" onClick={() => setIsCartOpen(false)}>
                            <button className="checkout-btn">Proceed to Checkout</button>
                        </Link>
                    </div>
                )}
            </div>
        </>
    );
}
