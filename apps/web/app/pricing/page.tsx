import { PricingPlans } from '@/components/pricing/PricingPlans';

export const metadata = { title: 'Pricing', description: 'Free and paid plans for privacy-first file scanning, metadata cleaning, verification, teams, and API usage.' };

export default function PricingPage() {
  return <main><PricingPlans /></main>;
}
