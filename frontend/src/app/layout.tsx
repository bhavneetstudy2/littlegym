import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import AppLayout from '@/components/AppLayout'
import { AuthProvider } from '@/contexts/AuthContext'
import { CenterContextProvider } from '@/contexts/CenterContext'
import { StudentLookupProvider } from '@/contexts/StudentLookupContext'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'The Little Gym CRM',
  description: 'Multi-tenant CRM for The Little Gym centers',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <CenterContextProvider>
            <StudentLookupProvider>
              <AppLayout>{children}</AppLayout>
            </StudentLookupProvider>
          </CenterContextProvider>
        </AuthProvider>
      </body>
    </html>
  )
}
