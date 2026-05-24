export function PricingCard({ name, price, features }: { name: string; price: string; features: string[] }) {
  return <div className="card p-6"><h3 className="text-xl font-bold text-ink">{name}</h3><p className="mt-3 text-3xl font-bold text-ink">{price}</p><ul className="mt-5 space-y-2 text-sm text-subtle">{features.map((feature) => <li key={feature}>• {feature}</li>)}</ul></div>;
}
