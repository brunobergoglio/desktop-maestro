import { NextRequest, NextResponse } from 'next/server';

const BACKEND = process.env.API_URL || 'http://127.0.0.1:7899';

export async function GET(req: NextRequest) {
  const path = req.nextUrl.pathname.replace('/api/desktopmaestro', '');
  const search = req.nextUrl.search;
  try {
    const res = await fetch(`${BACKEND}${path}${search}`, {
      headers: { 'Accept': 'application/json' },
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (e: any) {
    return NextResponse.json(
      { error: `Backend unreachable: ${e.message}` },
      { status: 503 }
    );
  }
}

export async function POST(req: NextRequest) {
  const path = req.nextUrl.pathname.replace('/api/desktopmaestro', '');
  const body = await req.json().catch(() => ({}));
  try {
    const res = await fetch(`${BACKEND}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (e: any) {
    return NextResponse.json(
      { error: `Backend unreachable: ${e.message}` },
      { status: 503 }
    );
  }
}

export async function PUT(req: NextRequest) {
  const path = req.nextUrl.pathname.replace('/api/desktopmaestro', '');
  const body = await req.json().catch(() => ({}));
  try {
    const res = await fetch(`${BACKEND}${path}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (e: any) {
    return NextResponse.json(
      { error: `Backend unreachable: ${e.message}` },
      { status: 503 }
    );
  }
}
