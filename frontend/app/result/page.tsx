"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { FPRSResponse, MedicamentoDetalhe } from "@/lib/types";
import Link from "next/link";

function Badge({ text, variant }: { text: string; variant: "red" | "yellow" | "green" | "gray" | "blue" }) {
  const styles: Record<string, string> = {
    red:    "bg-red-100 text-red-800 border-red-200",
    yellow: "bg-yellow-100 text-yellow-800 border-yellow-200",
    green:  "bg-green-100 text-green-800 border-green-200",
    gray:   "bg-gray-100 text-gray-600 border-gray-200",
    blue:   "bg-blue-100 text-blue-800 border-blue-200",
  };
  return (
    <span className={`inline-block text-xs font-medium border rounded-full px-2 py-0.5 ${styles[variant]}`}>
      {text}
    </span>
  );
}

function AfinidadeBadge({ v }: { v: string }) {
  if (v === "High")     return <Badge text="Alta" variant="red" />;
  if (v === "Moderate") return <Badge text="Moderada" variant="yellow" />;
  if (v === "Low")      return <Badge text="Baixa" variant="blue" />;
  return <span className="text-gray-400 text-xs">—</span>;
}

function MedicamentoRow({ m }: { m: MedicamentoDetalhe }) {
  const naoEncontrado = !m.encontrado;
  const duplicata = m.duplicata;

  return (
    <tr className={naoEncontrado ? "bg-yellow-50" : duplicata ? "bg-gray-50 opacity-60" : ""}>
      <td className="px-3 py-2 text-sm">
        {m.entrada_original !== m.nome_normalizado ? (
          <span>
            {m.entrada_original}{" "}
            <span className="text-xs text-gray-400">→ {m.nome_normalizado}</span>
          </span>
        ) : (
          m.entrada_original
        )}
      </td>
      <td className="px-3 py-2 text-center">
        {naoEncontrado ? (
          <Badge text="Não encontrado" variant="yellow" />
        ) : duplicata ? (
          <Badge text="Duplicata" variant="gray" />
        ) : (
          <Badge text="Sim" variant="green" />
        )}
      </td>
      <td className="px-3 py-2 text-center">
        <AfinidadeBadge v={m.afinidade_ac} />
      </td>
      <td className="px-3 py-2 text-center">
        <AfinidadeBadge v={m.afinidade_sedativa} />
      </td>
      <td className="px-3 py-2 text-center text-sm font-mono">
        {m.contribuicao > 0 ? (
          <span className="font-semibold text-gray-900">{m.contribuicao.toFixed(1)}</span>
        ) : (
          <span className="text-gray-400">0</span>
        )}
      </td>
      <td className="px-3 py-2 text-xs text-gray-500">{m.observacao}</td>
    </tr>
  );
}

export default function ResultPage() {
  const router = useRouter();
  const [result, setResult] = useState<FPRSResponse | null>(null);

  useEffect(() => {
    const raw = sessionStorage.getItem("fprs_result");
    if (!raw) {
      router.replace("/");
      return;
    }
    setResult(JSON.parse(raw));
  }, [router]);

  if (!result) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-500">Carregando…</p>
      </main>
    );
  }

  const altoRisco = result.categoria === "Alto risco";
  const naoEncontrados = result.medicamentos.filter((m) => !m.encontrado);

  return (
    <main className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-4xl mx-auto space-y-6">

        {/* Cabeçalho */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Resultado FPRS</h1>
            {result.paciente_id && (
              <p className="text-sm text-gray-500 mt-0.5">Paciente: {result.paciente_id}</p>
            )}
          </div>
          <Link
            href="/"
            className="text-sm text-blue-600 hover:underline"
          >
            ← Nova avaliação
          </Link>
        </div>

        {/* Card de classificação */}
        <div
          className={`rounded-xl border-2 p-6 ${
            altoRisco
              ? "border-red-400 bg-red-50"
              : "border-green-400 bg-green-50"
          }`}
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-gray-600 mb-1">FPRS Final</p>
              <p
                className={`text-5xl font-black ${
                  altoRisco ? "text-red-700" : "text-green-700"
                }`}
              >
                {result.fprs.toFixed(1)}
              </p>
              <p
                className={`mt-2 text-lg font-semibold ${
                  altoRisco ? "text-red-700" : "text-green-700"
                }`}
              >
                {result.categoria}
              </p>
              <p className={`text-sm mt-1 ${altoRisco ? "text-red-600" : "text-green-600"}`}>
                {result.alerta}
              </p>
            </div>

            {/* Componentes */}
            <div className="text-sm space-y-2 min-w-[200px]">
              <div className="flex justify-between gap-8">
                <span className="text-gray-500">Medicamentos</span>
                <span className="font-mono font-semibold">{result.total_medicamentos}</span>
              </div>
              <div className="flex justify-between gap-8">
                <span className="text-gray-500">{result.label_polifarmacia}</span>
                <span className="font-mono font-semibold">+{result.pontos_polifarmacia.toFixed(1)}</span>
              </div>
              <div className="flex justify-between gap-8">
                <span className="text-gray-500">Carga AC/sedativa</span>
                <span className="font-mono font-semibold">+{result.carga_afinidade.toFixed(1)}</span>
              </div>
              <div className="flex justify-between gap-8">
                <span className="text-gray-500">MPI/Beers adicional</span>
                <span className="font-mono font-semibold">+{result.pim_adicional.toFixed(1)}</span>
              </div>
              {result.idade && (
                <div className="flex justify-between gap-8">
                  <span className="text-gray-500">Idade</span>
                  <span className="font-mono">{result.idade} anos</span>
                </div>
              )}
              {result.data_avaliacao && (
                <div className="flex justify-between gap-8">
                  <span className="text-gray-500">Data</span>
                  <span className="font-mono">{result.data_avaliacao}</span>
                </div>
              )}
            </div>
          </div>
          {result.observacao && (
            <p className="mt-4 text-sm text-gray-600 border-t border-gray-200 pt-3">
              {result.observacao}
            </p>
          )}
        </div>

        {/* Alerta de não encontrados */}
        {naoEncontrados.length > 0 && (
          <div className="rounded-lg border border-yellow-300 bg-yellow-50 px-4 py-3">
            <p className="text-sm font-semibold text-yellow-800 mb-1">
              {naoEncontrados.length} medicamento(s) não encontrado(s) na base
            </p>
            <p className="text-xs text-yellow-700">
              Revisar grafia ou nome genérico:{" "}
              <span className="font-mono">
                {naoEncontrados.map((m) => m.entrada_original).join(", ")}
              </span>
            </p>
          </div>
        )}

        {/* Tabela detalhada */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100">
            <h2 className="text-sm font-semibold text-gray-700">Detalhamento por medicamento</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                <tr>
                  <th className="px-3 py-2">Medicamento</th>
                  <th className="px-3 py-2 text-center">Na base?</th>
                  <th className="px-3 py-2 text-center">Afinidade AC</th>
                  <th className="px-3 py-2 text-center">Afinidade Sed.</th>
                  <th className="px-3 py-2 text-center">Contribuição</th>
                  <th className="px-3 py-2">Observação</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {result.medicamentos.map((m, i) => (
                  <MedicamentoRow key={i} m={m} />
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </main>
  );
}
