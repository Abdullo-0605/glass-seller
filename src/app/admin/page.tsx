'use client';

import { useState, useEffect } from 'react';
import { Package, Truck, ShoppingBag, DollarSign } from 'lucide-react';

interface Stats {
    totalProducts: number;
    totalShipments: number;
    pendingOrders: number;
    totalRevenue: number;
}

export default function AdminDashboard() {
    const [stats, setStats] = useState<Stats>({
        totalProducts: 0,
        totalShipments: 0,
        pendingOrders: 0,
        totalRevenue: 0,
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function load() {
            try {
                const [productsRes, shipmentsRes, ordersRes] = await Promise.all([
                    fetch('/api/products'),
                    fetch('/api/shipments'),
                    fetch('/api/orders'),
                ]);
                const products = await productsRes.json();
                const shipments = await shipmentsRes.json();
                const orders = await ordersRes.json();

                setStats({
                    totalProducts: products.length,
                    totalShipments: shipments.length,
                    pendingOrders: orders.filter((o: { status: string }) => o.status === 'PENDING').length,
                    totalRevenue: orders
                        .filter((o: { status: string }) => o.status === 'APPROVED')
                        .reduce((sum: number, o: { totalAmount: number }) => sum + o.totalAmount, 0),
                });
            } catch (err) {
                console.error('Failed to load stats', err);
            }
            setLoading(false);
        }
        load();
    }, []);

    if (loading) {
        return (
            <div className="loading">
                <div className="spinner" />
            </div>
        );
    }

    return (
        <div>
            <div className="admin-header">
                <h1>Dashboard</h1>
            </div>

            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-card-icon blue"><Package size={22} /></div>
                    <div className="stat-card-value">{stats.totalProducts}</div>
                    <div className="stat-card-label">Total Products</div>
                </div>
                <div className="stat-card">
                    <div className="stat-card-icon green"><Truck size={22} /></div>
                    <div className="stat-card-value">{stats.totalShipments}</div>
                    <div className="stat-card-label">Wholesale Shipments</div>
                </div>
                <div className="stat-card">
                    <div className="stat-card-icon yellow"><ShoppingBag size={22} /></div>
                    <div className="stat-card-value">{stats.pendingOrders}</div>
                    <div className="stat-card-label">Pending Orders</div>
                </div>
                <div className="stat-card">
                    <div className="stat-card-icon red"><DollarSign size={22} /></div>
                    <div className="stat-card-value">${stats.totalRevenue.toFixed(2)}</div>
                    <div className="stat-card-label">Approved Revenue</div>
                </div>
            </div>
        </div>
    );
}
