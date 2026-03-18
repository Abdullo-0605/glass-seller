'use client';

import { useState } from 'react';
import { useCart } from '@/context/CartContext';
import { ShoppingCart, Check, Package } from 'lucide-react';

interface Product {
    id: string;
    name: string;
    description: string;
    category: string;
    price: number;
    stockQuantity: number;
    imageUrl: string;
}

export default function ProductCard({ product }: { product: Product }) {
    const { addItem } = useCart();
    const [justAdded, setJustAdded] = useState(false);

    const handleAdd = () => {
        if (product.stockQuantity <= 0) return;
        addItem({
            id: product.id,
            name: product.name,
            price: product.price,
            imageUrl: product.imageUrl,
        });
        setJustAdded(true);
        setTimeout(() => setJustAdded(false), 1200);
    };

    const stockLabel =
        product.stockQuantity <= 0
            ? 'Out of stock'
            : product.stockQuantity <= 5
                ? `Only ${product.stockQuantity} left`
                : `${product.stockQuantity} in stock`;

    const stockClass =
        product.stockQuantity <= 0 ? 'out' : product.stockQuantity <= 5 ? 'low' : '';

    return (
        <div className="product-card">
            <div className="product-card-image">
                {product.imageUrl ? (
                    <img src={product.imageUrl} alt={product.name} />
                ) : (
                    <Package size={48} />
                )}
            </div>
            <div className="product-card-body">
                <span className="product-card-category">{product.category}</span>
                <h3 className="product-card-name">{product.name}</h3>
                <p className="product-card-desc">{product.description}</p>
                <div className="product-card-footer">
                    <div>
                        <div className="product-card-price">${product.price.toFixed(2)}</div>
                        <div className={`product-card-stock ${stockClass}`}>{stockLabel}</div>
                    </div>
                    <button
                        className={`add-to-cart-btn ${justAdded ? 'added' : ''}`}
                        onClick={handleAdd}
                        disabled={product.stockQuantity <= 0}
                    >
                        {justAdded ? <Check size={16} /> : <ShoppingCart size={16} />}
                        {justAdded ? 'Added!' : 'Add'}
                    </button>
                </div>
            </div>
        </div>
    );
}
