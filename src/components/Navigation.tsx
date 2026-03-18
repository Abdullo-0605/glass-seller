'use client';

import Link from 'next/link';
import { useCart } from '@/context/CartContext';
import { ShoppingCart, Gem, LayoutDashboard } from 'lucide-react';

export default function Navigation() {
    const { totalItems, setIsCartOpen } = useCart();

    return (
        <nav className="nav">
            <div className="nav-inner">
                <Link href="/" className="nav-brand">
                    <div className="nav-brand-icon">
                        <Gem size={22} />
                    </div>
                    GlassVault
                </Link>

                <div className="nav-links">
                    <Link href="/" className="nav-link">
                        Catalog
                    </Link>
                    <Link href="/admin" className="nav-link">
                        <LayoutDashboard size={16} />
                        Team Dashboard
                    </Link>
                    <button className="nav-cart-btn" onClick={() => setIsCartOpen(true)}>
                        <ShoppingCart size={18} />
                        Cart
                        {totalItems > 0 && <span className="cart-badge">{totalItems}</span>}
                    </button>
                </div>
            </div>
        </nav>
    );
}
