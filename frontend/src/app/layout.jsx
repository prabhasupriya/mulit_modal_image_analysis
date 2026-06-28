import "./globals.css";

export const metadata = {
  title: "Multi-Modal AI Platform",
  description: "Vision analysis and image generation, orchestrated.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
