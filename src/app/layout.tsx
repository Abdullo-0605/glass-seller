import type { Metadata } from "next";
import "./globals.css";
import { CartProvider } from "@/context/CartContext";
import Navigation from "@/components/Navigation";
import CartDrawer from "@/components/CartDrawer";

export const metadata: Metadata = {
  title: "GlassVault | Premium Glass Parts & Supplies",
  description: "Browse and order premium glass parts. Windshields, tempered glass, mirrors, and more — all available for quick team-approved fulfillment.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <CartProvider>
          <Navigation />
          <CartDrawer />
          {children}
        </CartProvider>
      </body>
    </html>
  );
}
