"use client";

import { useEffect, useState } from "react";

export function HealthStatus() {
  const [label, setLabel] = useState("API …");

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    fetch(`${base}/health`)
      .then((response) => response.json())
      .then((data: { status?: string }) => {
        setLabel(data.status === "ok" ? "API ok" : "API down");
      })
      .catch(() => setLabel("API down"));
  }, []);

  return <p>{label}</p>;
}
