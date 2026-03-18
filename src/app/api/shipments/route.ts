import { prisma } from '@/lib/prisma';
import { NextRequest, NextResponse } from 'next/server';

export async function GET() {
    const shipments = await prisma.wholesaleShipment.findMany({
        include: { items: { include: { product: true } } },
        orderBy: { createdAt: 'desc' },
    });
    return NextResponse.json(shipments);
}

export async function POST(request: NextRequest) {
    const body = await request.json();

    const shipment = await prisma.wholesaleShipment.create({
        data: {
            supplier: body.supplier,
            invoiceNumber: body.invoiceNumber || '',
            totalCost: parseFloat(body.totalCost),
            notes: body.notes || '',
            status: 'PENDING',
            items: {
                create: body.items.map((item: { productId: string; quantity: number; unitCost: number }) => ({
                    productId: item.productId,
                    quantity: parseInt(String(item.quantity)),
                    unitCost: parseFloat(String(item.unitCost)),
                })),
            },
        },
        include: { items: { include: { product: true } } },
    });

    return NextResponse.json(shipment, { status: 201 });
}
