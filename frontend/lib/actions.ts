"use server";

import { FPRSResponse } from "./types";

const API_URL = process.env.API_URL ?? "http://localhost:8000";

export async function calcularFPRS(formData: FormData): Promise<FPRSResponse> {
  const raw = formData.get("medicamentos") as string;
  const medicamentos = raw
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);

  const payload = {
    medicamentos,
    paciente_id: (formData.get("paciente_id") as string) || null,
    idade: formData.get("idade") ? Number(formData.get("idade")) : null,
    data_avaliacao: (formData.get("data_avaliacao") as string) || null,
    observacao: (formData.get("observacao") as string) || null,
  };

  const res = await fetch(`${API_URL}/calcular`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail ?? `Erro ${res.status} ao calcular FPRS`);
  }

  return res.json() as Promise<FPRSResponse>;
}
