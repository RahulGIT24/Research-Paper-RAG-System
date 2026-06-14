import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
    const hasToken = request.cookies.has('access_token');

    const path = request.nextUrl.pathname;

    const isAuthPage = path === '/' || 
        path.startsWith('/signin') ||
        path.startsWith('/signup') ||
        path.startsWith('/verify') ||
        path.startsWith('/forgot-password') ||
        path.startsWith('/reset-password');

    const isProtectedPage = path.startsWith('/dashboard');

    if (hasToken && isAuthPage) {
        return NextResponse.redirect(new URL('/dashboard', request.url));
    }

    if (!hasToken && isProtectedPage) {
        return NextResponse.redirect(new URL('/signin', request.url));
    }

    return NextResponse.next();
}

export const config = {
    matcher: ['/dashboard/:path*', '/signin', '/signup', '/verify', '/forgot-password', '/reset-password','/'],
};