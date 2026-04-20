package com.example.ordersystem.common.api;

import java.util.List;

public class PageResponse<T> {

    private final List<T> items;
    private final long total;
    private final int page;
    private final int size;

    private PageResponse(List<T> items, long total, int page, int size) {
        this.items = items;
        this.total = total;
        this.page = page;
        this.size = size;
    }

    public static <T> PageResponse<T> of(List<T> items, long total, int page, int size) {
        return new PageResponse<>(items, total, page, size);
    }

    public List<T> getItems() {
        return items;
    }

    public long getTotal() {
        return total;
    }

    public int getPage() {
        return page;
    }

    public int getSize() {
        return size;
    }
}
