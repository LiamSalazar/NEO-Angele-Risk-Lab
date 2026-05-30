import { Badge } from "@/components/ui/badge";
import { riskTone } from "@/lib/risk";
import { cn } from "@/lib/utils";

type RiskCategoryBadgeProps = {
  category?: string | null;
};

export function RiskCategoryBadge({ category }: RiskCategoryBadgeProps) {
  const tone = riskTone(category);

  return (
    <Badge className={cn(tone.bgClass, tone.borderClass, tone.textClass)} data-testid="risk-category-badge">
      {tone.label}
    </Badge>
  );
}
