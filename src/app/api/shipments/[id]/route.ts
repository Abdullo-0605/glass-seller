import { prisma } from '@/lib/prisma';
import { NextRequest, NextResponse } from 'next/server';

export async function PUT(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    const { id } = await params;
    const body = await request.json();

    if (body.status === 'RECEIVED') {
        // When marking as received, update product stock
        const shipment = await prisma.wholesaleShipment.findUnique({
            where: { id },
            include: { items: true },
        });

        if (!shipment) return NextResponse.json({ error: 'Not found' }, { status: 404 });
        if (shipment.status === 'RECEIVED') {
            return NextResponse.json({ error: 'Already received' }, { status: 400 });
        }

        // Update stock for each item
        for (const item of shipment.items) {
            await prisma.product.update({
                where: { id: item.productId },
                data: { stockQuantity: { increment: item.quantity } },
            });
        }

        const updated = await prisma.wholesaleShipment.update({
            where: { id },
            data: { status: 'RECEIVED' },
            include: { items: { include: { product: true } } },
        });

        return NextResponse.json(updated);
    }

    const updated = await prisma.wholesaleShipment.update({
        where: { id },
        data: { status: body.status },
        include: { items: { include: { product: true } } },
    });

    return NextResponse.json(updated);
}

export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    const { id } = await params;
    await prisma.wholesaleShipment.delete({ where: { id } });
    return NextResponse.json({ success: true });
}
