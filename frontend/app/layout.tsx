import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Lang-to-NX',
  description: '自然语言驱动 Siemens NX 建模',
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
