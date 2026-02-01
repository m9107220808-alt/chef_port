-- Миграция: добавление таблицы рекомендаций товаров
-- Дата: 2026-02-01

-- Таблица связей товаров (рекомендации)
CREATE TABLE IF NOT EXISTS product_recommendations (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    recommended_product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    recommendation_type VARCHAR(20) DEFAULT 'cross-sell', -- cross-sell, upsell, combo
    priority INT DEFAULT 1, -- 1=высокий, 2=средний, 3=низкий
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(product_id, recommended_product_id)
);

CREATE INDEX IF NOT EXISTS idx_product_recommendations_product ON product_recommendations(product_id);
CREATE INDEX IF NOT EXISTS idx_product_recommendations_type ON product_recommendations(recommendation_type);
