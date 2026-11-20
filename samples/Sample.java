package com.example.shop;

import java.util.List;
import java.util.Map;

@Entity
@Table(name = "orders")
public class Sample<T extends Comparable<T>> {
    private static final int MAX_ITEMS = 100;
    private final Map<String, List<T>> index;
    private double[] weights;

    public Sample(Map<String, List<T>> index) {
        this.index = index;
    }

    @Override
    public String toString() {
        return "Sample" + index.size();
    }

    @Deprecated
    public <R> List<R> convert(List<T> items, boolean strict, long limit) {
        int count = 0;
        char[] buffer = new char[16];
        for (T item : items) {
            if (strict && count > limit) {
                break;
            }
            count++;
        }
        return null;
    }
}
