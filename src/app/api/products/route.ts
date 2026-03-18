import { prisma } from '@/lib/prisma';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
    const { searchParams } = new URL(request.url);
    const search = searchParams.get('search') || '';
    const category = searchParams.get('category') || '';

    const where: Record<string, unknown> = {};

    if (search) {
        where.OR = [
            { name: { contains: search } },
            { description: { contains: search } },
        ];
    }

    if (category && category !== 'All') {
        where.category = category;
    }

    const products = await prisma.product.findMany({
        where,
        orderBy: { createdAt: 'desc' },
    });

    return NextResponse.json(products);
}

export async function POST(request: NextRequest) {
    const body = await request.json();
    const product = await prisma.product.create({
        data: {
            name: body.name,
            description: body.description || '',
            category: body.category || 'General',
            price: parseFloat(body.price),
            stockQuantity: parseInt(body.stockQuantity) || 0,
            imageUrl: body.imageUrl || '',
        },
    });
    return NextResponse.json(product, { status: 201 });
}
