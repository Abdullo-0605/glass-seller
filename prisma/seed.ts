import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
    console.log('🌱 Seeding database...');

    // Clear existing data
    await prisma.orderItem.deleteMany();
    await prisma.order.deleteMany();
    await prisma.shipmentItem.deleteMany();
    await prisma.wholesaleShipment.deleteMany();
    await prisma.product.deleteMany();

    // Create sample glass products
    const products = await Promise.all([
        prisma.product.create({
            data: {
                name: 'Front Windshield - Toyota Camry 2020-2024',
                description: 'OEM-quality laminated front windshield glass for Toyota Camry models 2020 through 2024. UV protection and acoustic dampening included.',
                category: 'Windshield',
                price: 289.99,
                stockQuantity: 15,
                imageUrl: '',
            },
        }),
        prisma.product.create({
            data: {
                name: 'Rear Windshield - Honda Civic 2019-2023',
                description: 'Tempered rear glass with defroster grid for Honda Civic sedan. Heat-treated for maximum safety.',
                category: 'Windshield',
                price: 199.99,
                stockQuantity: 8,
                imageUrl: '',
            },
        }),
        prisma.product.create({
            data: {
                name: 'Side Window - Ford F-150 Driver Front',
                description: 'Tempered driver-side front window for Ford F-150 2018-2023. Power window compatible with anti-pinch technology.',
                category: 'Window',
                price: 149.99,
                stockQuantity: 22,
                imageUrl: '',
            },
        }),
        prisma.product.create({
            data: {
                name: 'Tempered Glass Panel 12x24"',
                description: 'Custom-cut tempered glass panel, 12 by 24 inches. 3/8" thick, suitable for shelving, tabletops, and decorative use.',
                category: 'Tempered Glass',
                price: 45.99,
                stockQuantity: 50,
                imageUrl: '',
            },
        }),
        prisma.product.create({
            data: {
                name: 'Beveled Edge Mirror 36x48"',
                description: 'Premium beveled-edge mirror with 1-inch bevel. Crystal-clear reflection, suitable for bathroom or decorative installations.',
                category: 'Mirror',
                price: 129.99,
                stockQuantity: 12,
                imageUrl: '',
            },
        }),
        prisma.product.create({
            data: {
                name: 'Frameless Shower Door Panel 34x72"',
                description: '10mm clear tempered glass shower door panel. Frameless design with polished edges and pre-drilled hinge holes.',
                category: 'Tempered Glass',
                price: 349.99,
                stockQuantity: 5,
                imageUrl: '',
            },
        }),
        prisma.product.create({
            data: {
                name: 'Windshield Repair Kit - Professional',
                description: 'Complete windshield chip repair kit for professionals. Includes resin, injector, curing strips, and UV light.',
                category: 'Accessories',
                price: 34.99,
                stockQuantity: 40,
                imageUrl: '',
            },
        }),
        prisma.product.create({
            data: {
                name: 'Safety Glass Film Roll - 60" Wide',
                description: 'Clear safety glass film, 60 inches wide, sold per linear foot. Holds glass fragments together on impact. ANSI Z97.1 certified.',
                category: 'Accessories',
                price: 12.99,
                stockQuantity: 100,
                imageUrl: '',
            },
        }),
        prisma.product.create({
            data: {
                name: 'Quarter Glass - Chevrolet Suburban 2021+',
                description: 'Fixed quarter glass panel for rear side windows. OEM-spec tinted tempered glass with rubber seal included.',
                category: 'Window',
                price: 89.99,
                stockQuantity: 18,
                imageUrl: '',
            },
        }),
        prisma.product.create({
            data: {
                name: 'Custom Cut Mirror - Per Sq Ft',
                description: 'Custom-cut mirror glass, priced per square foot. Specify dimensions at checkout. Available in clear, bronze, or grey tint.',
                category: 'Mirror',
                price: 18.99,
                stockQuantity: 200,
                imageUrl: '',
            },
        }),
        prisma.product.create({
            data: {
                name: 'Insulated Glass Unit 24x36" Double Pane',
                description: 'Energy-efficient double pane insulated glass unit. Argon gas filled with Low-E coating. Ideal for window replacements.',
                category: 'Window',
                price: 159.99,
                stockQuantity: 10,
                imageUrl: '',
            },
        }),
        prisma.product.create({
            data: {
                name: 'Glass Suction Cup Lifter - Triple Cup',
                description: 'Heavy-duty triple suction cup glass lifter. Rated for up to 150 lbs. Ergonomic handle with quick-release lever.',
                category: 'Accessories',
                price: 49.99,
                stockQuantity: 25,
                imageUrl: '',
            },
        }),
    ]);

    console.log(`✅ Created ${products.length} products`);

    // Create a sample wholesale shipment
    const shipment = await prisma.wholesaleShipment.create({
        data: {
            supplier: 'Pacific Glass Distributors',
            invoiceNumber: 'PGD-2024-0312',
            totalCost: 2450.00,
            status: 'RECEIVED',
            notes: 'March 2024 restock order',
            items: {
                create: [
                    { productId: products[0].id, quantity: 10, unitCost: 145.00 },
                    { productId: products[1].id, quantity: 5, unitCost: 100.00 },
                    { productId: products[2].id, quantity: 10, unitCost: 75.00 },
                ],
            },
        },
    });

    console.log(`✅ Created sample shipment: ${shipment.invoiceNumber}`);

    // Create a sample pending order
    const order = await prisma.order.create({
        data: {
            customerName: 'Mike Johnson',
            customerEmail: 'mike.johnson@email.com',
            customerPhone: '(555) 987-6543',
            customerAddress: '456 Oak Ave, Springfield, IL 62704',
            totalAmount: 579.97,
            status: 'PENDING',
            notes: 'Need installation by Friday if possible.',
            items: {
                create: [
                    { productId: products[0].id, quantity: 1, price: 289.99 },
                    { productId: products[4].id, quantity: 1, price: 129.99 },
                    { productId: products[2].id, quantity: 1, price: 149.99 },
                ],
            },
        },
    });

    console.log(`✅ Created sample order from ${order.customerName}`);

    console.log('\n🎉 Seed complete!');
}

main()
    .catch(console.error)
    .finally(() => prisma.$disconnect());
