<?php

declare(strict_types=1);

namespace Example\Shop;

use Attribute;

#[Attribute(Attribute::TARGET_CLASS)]
final class Sample
{
    public function __construct(
        private readonly int $max,
        private ?string $name = null,
    ) {
    }

    #[Deprecated]
    public function compute(array $items, bool $strict, float $factor = 1.0): int|float
    {
        $total = 0;
        foreach ($items as $item) {
            if ($strict && $item > $this->max) {
                continue;
            }
            $total += $item * $factor;
        }
        return $total;
    }
}
?>
<p>Total: <?= $total ?></p>
