import { cookies } from "next/headers";
import { redirect } from "next/navigation";

function hasRefreshCookie() {
  const jar = cookies();
  return Boolean(
    jar.get("refresh_token") ||
      jar.get("gtm_refresh_token") ||
      jar.get("__Host-refresh_token") ||
      jar.get("__Host-gtm_refresh_token")
  );
}

export default function HomePage() {
  redirect(hasRefreshCookie() ? "/" : "/login");
}
