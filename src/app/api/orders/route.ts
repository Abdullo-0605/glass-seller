import { prisma } from '@/lib/prisma';
import { NextRequest, NextResponse } from 'next/server';

export async function GET() {
    const orders = await prisma.order.findMany({
        include: { items: { include: { product: true } } },
        orderBy: { createdAt: 'desc' },
    });
    return NextResponse.json(orders);
}

export async function POST(request: NextRequest) {
    const body = await request.json();

    // Validate stock availability
    for (const item of body.items) {
        const product = await prisma.product.findUnique({ where: { id: item.productId } });
        if (!product) {
            return NextResponse.json({ error: `Product ${item.productId} not found` }, { status: 400 });
        }
        if (product.stockQuantity < item.quantity) {
            return NextResponse.json(
                { error: `Insufficient stock for ${product.name}. Available: ${product.stockQuantity}` },
                { status: 400 }
            );
        }
    }

    const order = await prisma.order.create({
        data: {
            customerName: body.customerName,
            customerEmail: body.customerEmail,
            customerPhone: body.customerPhone || '',
            customerAddress: body.customerAddress || '',
            totalAmount: parseFloat(body.totalAmount),
            notes: body.notes || '',
            status: 'PENDING',
            items: {
                create: body.items.map((item: { productId: string; quantity: number; price: number }) => ({
                    productId: item.productId,
                    quantity: parseInt(String(item.quantity)),
                    price: parseFloat(String(item.price)),
                })),
            },
        },
        include: { items: { include: { product: true } } },
    });

    return NextResponse.json(order, { status: 201 });
}
