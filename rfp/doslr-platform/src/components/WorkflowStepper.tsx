type Props = {
  steps: string[];
  activeStep: number;
};

export default function WorkflowStepper({ steps, activeStep }: Props) {
  return (
    <div className="grid gap-2 sm:grid-cols-5">
      {steps.map((step, index) => {
        const isDone = index < activeStep;
        const isCurrent = index === activeStep && activeStep < steps.length;
        return (
          <div
            key={step}
            className={`rounded-xl border px-3 py-2 text-xs ${
              isCurrent
                ? "border-sky-300 bg-sky-50 text-sky-800"
                : isDone
                  ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                  : "border-slate-200 bg-white text-slate-500"
            }`}
          >
            <p className="font-semibold">Step {index + 1}</p>
            <p className="mt-0.5">{step}</p>
          </div>
        );
      })}
    </div>
  );
}
