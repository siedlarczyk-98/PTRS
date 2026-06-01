import FPRSForm from "@/components/FPRSForm";

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">
            FPRS — Escore de Risco Farmacoterapêutico Funcional
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Modelo 3 · Sobrecarga anticolinérgica/sedativa + Critérios Beers 2023
          </p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <FPRSForm />
        </div>
      </div>
    </main>
  );
}
