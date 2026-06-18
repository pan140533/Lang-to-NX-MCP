import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Text-to-CAD',
  description: 'AI-driven CAD generation',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh">
      <body>{children}</body>
    </html>
  )
}
