import { NextRequest, NextResponse } from "next/server";

const BACKEND_ORIGIN = (process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(
  /\/$/,
  ""
);

async function proxy(request: NextRequest, method: string) {
  const targetUrl = new URL(request.nextUrl.pathname.replace(/^\/api/, ""), BACKEND_ORIGIN);
  targetUrl.search = request.nextUrl.search;

  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("content-length");

  const body = method === "GET" || method === "HEAD" ? undefined : await request.arrayBuffer();
  const response = await fetch(targetUrl, {
    method,
    headers,
    body,
    redirect: "manual"
  });

  return new NextResponse(response.body, {
    status: response.status,
    headers: response.headers
  });
}

export function GET(request: NextRequest) {
  return proxy(request, "GET");
}

export function POST(request: NextRequest) {
  return proxy(request, "POST");
}

export function PUT(request: NextRequest) {
  return proxy(request, "PUT");
}

export function PATCH(request: NextRequest) {
  return proxy(request, "PATCH");
}

export function DELETE(request: NextRequest) {
  return proxy(request, "DELETE");
}

export function OPTIONS(request: NextRequest) {
  return proxy(request, "OPTIONS");
}
