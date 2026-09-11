const CARDS = [
  {
    icon: "📏",
    title: "Hair Length Chart",
    body: "From 12\" to 30\" - measured tip to root so you know exactly what to expect on arrival.",
  },
  {
    icon: "🌊",
    title: "Textures & Styles",
    body: "Straight, body wave, deep wave, curly, and kinky curly - every texture sourced from single-donor Vietnamese hair.",
  },
  {
    icon: "🎨",
    title: "Hair Color Chart",
    body: "Natural black through to blonde and custom ombre - color-matched before it leaves our quality-control office.",
  },
];

export function InfoCards() {
  return (
    <div className="mx-auto grid max-w-6xl grid-cols-1 gap-4 px-6 py-10 sm:grid-cols-3">
      {CARDS.map((card) => (
        <div key={card.title} className="flex gap-4 rounded-lg border border-brand-border bg-brand-surface p-5">
          <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-brand-accent-soft text-xl">
            {card.icon}
          </span>
          <div>
            <p className="font-medium text-brand-ink">{card.title}</p>
            <p className="mt-1 text-sm text-brand-muted">{card.body}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
