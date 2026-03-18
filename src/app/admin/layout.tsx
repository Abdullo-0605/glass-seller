'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Package, Truck, ShoppingBag, ArrowLeft, Gem } from 'lucide-react';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();

    const links = [
        { href: '/admin', label: 'Dashboard', icon: LayoutDashboard },
        { href: '/admin/products', label: 'Products', icon: Package },
        { href: '/admin/shipments', label: 'Shipments', icon: Truck },
        { href: '/admin/orders', label: 'Customer Orders', icon: ShoppingBag },
    ];

    return (
        <div className="admin-layout">
            <aside className="admin-sidebar">
                <Link href="/admin" className="admin-sidebar-brand">
                    <div className="admin-sidebar-brand-icon">
                        <Gem size={18} />
                    </div>
                    GlassVault Admin
                </Link>

                <nav className="admin-nav">
                    {links.map(link => {
                        const Icon = link.icon;
                        const isActive = pathname === link.href;
                        return (
                            <Link
                                key={link.href}
                                href={link.href}
                                className={`admin-nav-link ${isActive ? 'active' : ''}`}
                            >
                                <Icon size={18} />
                                {link.label}
                            </Link>
                        );
                    })}
                </nav>

                <Link href="/" className="admin-back-link">
                    <ArrowLeft size={16} />
                    Back to Storefront
                </Link>
            </aside>

            <main className="admin-content">
                {children}
            </main>
        </div>
    );
}
