using System;
using System.Collections.Generic;

namespace Example.Shop;

[Serializable]
public class Sample
{
    private readonly int _max = 100;
    public string Name { get; set; }
    public List<decimal> Prices { get; } = new();

    [Obsolete("Use Total instead")]
    public double Compute(int count, bool strict, string label)
    {
        long total = 0;
        object boxed = label;
        byte[] data = new byte[8];
        foreach (var price in Prices)
        {
            if (strict && count > 0)
            {
                total += (long)price;
            }
        }
        return total;
    }
}
