export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(
    message: string,
    status: number,
    data: unknown,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
};

function getCookie(name: string): string | null {
  const cookies = document.cookie
    .split(";")
    .map((cookie) => cookie.trim());

  for (const cookie of cookies) {
    if (cookie.startsWith(`${name}=`)) {
      return decodeURIComponent(
        cookie.substring(name.length + 1),
      );
    }
  }

  return null;
}

async function parseResponse(
  response: Response,
): Promise<unknown> {
  const contentType =
    response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  const text = await response.text();

  return text || null;
}

function getErrorMessage(
  data: unknown,
  fallback: string,
): string {
  if (
    typeof data === "object" &&
    data !== null
  ) {
    if (
      "detail" in data &&
      typeof (data as { detail?: unknown }).detail ===
        "string"
    ) {
      return (data as { detail: string }).detail;
    }

    if (
      "message" in data &&
      typeof (data as { message?: unknown }).message ===
        "string"
    ) {
      return (data as { message: string }).message;
    }

    if (
      "error" in data &&
      typeof (data as { error?: unknown }).error ===
        "string"
    ) {
      return (data as { error: string }).error;
    }
  }

  return fallback;
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const method = (
    options.method ?? "GET"
  ).toUpperCase();

  const headers = new Headers(
    options.headers,
  );

  headers.set(
    "Accept",
    "application/json",
  );

  const hasBody =
    options.body !== undefined &&
    options.body !== null;

  if (
    hasBody &&
    !(options.body instanceof FormData)
  ) {
    headers.set(
      "Content-Type",
      "application/json",
    );
  }

  if (
    ![
      "GET",
      "HEAD",
      "OPTIONS",
      "TRACE",
    ].includes(method) &&
    !headers.has("X-CSRFToken")
  ) {
    const csrfToken = getCookie(
      "csrftoken",
    );

    if (csrfToken) {
      headers.set(
        "X-CSRFToken",
        csrfToken,
      );
    }
  }

  let body: BodyInit | undefined;

  if (hasBody) {
    if (options.body instanceof FormData) {
      body = options.body;
    } else {
      body = JSON.stringify(
        options.body,
      );
    }
  }

  let response: Response;

  try {
    response = await fetch(
      path,
      {
        ...options,
        method,
        headers,
        body,
        credentials: "include",
      },
    );
  } catch (error) {
    console.error(
      `API network error for ${method} ${path}:`,
      error,
    );

    throw new ApiError(
      "Unable to connect to the Sauti Yo server.",
      0,
      null,
    );
  }

  const data = await parseResponse(
    response,
  );

  if (!response.ok) {
    console.error(
      `API error for ${method} ${path}:`,
      response.status,
      data,
    );

    throw new ApiError(
      getErrorMessage(
        data,
        `Request failed with status ${response.status}.`,
      ),
      response.status,
      data,
    );
  }

  return data as T;
}

export async function ensureCsrfToken(): Promise<string> {
  const response =
    await apiRequest<{
      csrfToken: string;
    }>("/api/auth/csrf/");

  return response.csrfToken;
}