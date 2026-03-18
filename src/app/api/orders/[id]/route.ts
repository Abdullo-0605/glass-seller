import { prisma } from '@/lib/prisma';
import { NextRequest, NextResponse } from 'next/server';

export async function PUT(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    const { id } = await params;
    const body = await request.json();

    const order = await prisma.order.findUnique({
        where: { id },
        include: { items: true },
    });

    if (!order) return NextResponse.json({ error: 'Not found' }, { status: 404 });

    if (body.status === 'APPROVED' && order.status === 'PENDING') {
        // Deduct stock when order is approved
        for (const item of order.items) {
            const product = await prisma.product.findUnique({ where: { id: item.productId } });
            if (!product || product.stockQuantity < item.quantity) {
                return NextResponse.json(
                    { error: `Insufficient stock for product. Cannot approve.` },
                    { status: 400 }
                );
            }
            await prisma.product.update({
                where: { id: item.productId },
                data: { stockQuantity: { decrement: item.quantity } },
            });
        }
    }

    const updated = await prisma.order.update({
        where: { id },
        data: { status: body.status },
        include: { items: { include: { product: true } } },
    });

    return NextResponse.json(updated);
}
