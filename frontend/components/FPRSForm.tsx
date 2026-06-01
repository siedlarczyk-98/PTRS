"use client";

import { useActionState, useRef } from "react";
import { calcularFPRS } from "@/lib/actions";
import { FPRSResponse } from "@/lib/types";
import { useRouter } from "next/navigation";

type State = { error: string | null };

export default function FPRSForm() {
  const router = useRouter();
  const formRef = useRef<HTMLFormElement>(null);

  const [state, formAction, pending] = useActionState<State, FormData>(
    async (_prev, formData) => {
      try {
        const result = await calcularFPRS(formData);
        sessionStorage.setItem("fprs_result", JSON.stringify(result));
        router.push("/result");
        return { error: null };
      } catch (e: unknown) {
        return { error: e instanceof Error ? e.message : "Erro desconhecido" };
      }
    },
    { error: null }
  );

  return (
    <form ref={formRef} action={formAction} className="space-y-6">
      {/* Dados do paciente */}
      <fieldset className="border border-gray-200 rounded-lg p-4 space-y-4">
        <legend className="text-sm font-semibold text-gray-600 px-1">
          Dados do paciente (opcional)
        </legend>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              ID / Nome
            </label>
            <input
              name="paciente_id"
              type="text"
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Opcional"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Idade
            </label>
            <input
              name="idade"
              type="number"
              min={0}
              max={150}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Anos"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Data da avaliação
            </label>
            <input
              name="data_avaliacao"
              type="date"
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Observação
          </label>
          <input
            name="observacao"
            type="text"
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Anotação livre"
          />
        </div>
      </fieldset>

      {/* Lista de medicamentos */}
      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-1">
          Lista de medicamentos
          <span className="ml-1 font-normal text-gray-500">(um por linha, máx. 25)</span>
        </label>
        <textarea
          name="medicamentos"
          required
          rows={12}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
          placeholder={"amitriptyline\nlosartan\nmetformin\n..."}
        />
      </div>

      {state.error && (
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md px-3 py-2">
          {state.error}
        </p>
      )}

      <button
        type="submit"
        disabled={pending}
        className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-semibold py-2.5 rounded-lg transition-colors"
      >
        {pending ? "Calculando…" : "Calcular FPRS"}
      </button>
    </form>
  );
}
