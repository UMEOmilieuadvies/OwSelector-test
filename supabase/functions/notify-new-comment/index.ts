import { serve } from "https://deno.land/std@0.224.0/http/server.ts";

type CommentRecord = {
  message?: string;
  created_at?: string;
  app_version?: string;
  regulation?: string;
  article?: string;
};

type DatabaseWebhook = {
  type?: string;
  table?: string;
  schema?: string;
  record?: CommentRecord;
};

const REQUIRED_SECRET = Deno.env.get("COMMENT_WEBHOOK_SECRET") ?? "";
const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY") ?? "";
const EMAIL_FROM = Deno.env.get("COMMENT_EMAIL_FROM") ?? "";
const EMAIL_TO = Deno.env.get("COMMENT_EMAIL_TO") ?? "";

function escapeHtml(value: unknown): string {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function body(record: CommentRecord): string {
  const rows = [
    ["Opmerking", record.message],
    ["Geplaatst", record.created_at],
    ["Regeling", record.regulation],
    ["Artikel", record.article],
    ["Applicatieversie", record.app_version],
  ].filter(([, value]) => value);
  const tableRows = rows.map(([label, value]) =>
    "<tr><th align=\"left\">" + escapeHtml(label) + "</th><td>" + escapeHtml(value) + "</td></tr>"
  ).join("");

  return "<h1>Nieuwe opmerking — testomgeving</h1>" +
    "<p>Er is een nieuwe opmerking geplaatst in Omgevingswet Zoeker.</p>" +
    "<table>" + tableRows + "</table>" +
    "<p><a href=\"https://umeomilieuadvies.github.io/OwSelector-test/beheer.html\">Open het beheerscherm</a></p>";
}

serve(async (request) => {
  if (request.method !== "POST") {
    return Response.json({ error: "Alleen POST is toegestaan." }, { status: 405 });
  }
  if (!REQUIRED_SECRET || request.headers.get("x-comment-webhook-secret") !== REQUIRED_SECRET) {
    return Response.json({ error: "Ongeldige webhook." }, { status: 401 });
  }

  const event = (await request.json()) as DatabaseWebhook;
  if (event.type !== "INSERT" || event.schema !== "public" || event.table !== "comments") {
    return Response.json({ ignored: true });
  }
  if (!RESEND_API_KEY || !EMAIL_FROM || !EMAIL_TO) {
    console.error("E-mailmelding is niet volledig geconfigureerd.");
    return Response.json({ error: "E-mailmelding is niet geconfigureerd." }, { status: 503 });
  }

  const response = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: "Bearer " + RESEND_API_KEY,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: EMAIL_FROM,
      to: [EMAIL_TO],
      subject: "[TEST] Nieuwe opmerking Omgevingswet Zoeker",
      html: body(event.record ?? {}),
    }),
  });
  if (!response.ok) {
    console.error("Resend accepteerde de e-mail niet.", await response.text());
    return Response.json({ error: "E-mail kon niet worden verstuurd." }, { status: 502 });
  }
  return Response.json({ sent: true }, { status: 202 });
});
